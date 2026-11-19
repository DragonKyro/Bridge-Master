"""Parallel, resumable scraper for all 5 levels (540 deals) of BBO Bridge Master.

Saves one JSON file per deal organized by Level and Set (A/B/C/D):
  data/bbo_bridgemaster/
    index.json
    level_1_beginner/
      A/A-1.json .. A-36.json
      B/B-1.json .. B-30.json
    level_2_intermediate/
      A/A-1.json .. A-36.json
      B/B-1.json .. B-30.json
      C/C-1.json .. C-30.json
      D/D-1.json .. D-30.json
    level_3_advanced/
      A/ .. D/
    level_4_expert/
      A/ .. D/
    level_5_world_class/
      A/ .. C/
"""

from __future__ import annotations
import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
import websocket

REPO_ROOT = Path(__file__).resolve().parent.parent


def validate_deal_pbn(deal_pbn: str, title: str = "") -> list[str]:
    """Check a PBN deal ("S:hand hand hand hand"): 13 cards each, 52 distinct. Returns issues."""
    label = f"[{title}] " if title else ""
    try:
        _, rest = deal_pbn.split(":", 1)
        hands = rest.split()
        if len(hands) != 4:
            return [f"{label}expected 4 hands, got {len(hands)}"]
        issues, cards = [], []
        for h in hands:
            suits = h.split(".")
            if len(suits) != 4:
                return [f"{label}bad hand {h!r}"]
            hand = [s + r for s, ranks in zip("SHDC", suits) for r in ranks]
            if len(hand) != 13:
                issues.append(f"{label}hand {h!r} has {len(hand)} cards (need 13)")
            cards.extend(hand)
        if len(set(cards)) != 52:
            issues.append(f"{label}{len(set(cards))} unique cards (need 52)")
        return issues
    except Exception as e:  # noqa: BLE001
        return [f"{label}Parse error: {e}"]


LEVEL_CONFIG = {
    1: {
        "name": "Beginner",
        "folder": "level_1_beginner",
        "sets": ["A", "B"],
    },
    2: {
        "name": "Intermediate",
        "folder": "level_2_intermediate",
        "sets": ["A", "B", "C", "D"],
    },
    3: {
        "name": "Advanced",
        "folder": "level_3_advanced",
        "sets": ["A", "B", "C", "D"],
    },
    4: {
        "name": "Expert",
        "folder": "level_4_expert",
        "sets": ["A", "B", "C", "D"],
    },
    5: {
        "name": "World Class",
        "folder": "level_5_world_class",
        "sets": ["A", "B", "C"],
    },
}

BASE_OUT_DIR = REPO_ROOT / "data" / "bbo_bridgemaster"
RAW_DEALS_DIR = BASE_OUT_DIR / "raw_deals"

SUIT_SYMBOLS = {"♠": "S", "♥": "H", "♦": "D", "♣": "C"}
PRINT_LOCK = threading.Lock()


def log(msg: str) -> None:
    with PRINT_LOCK:
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)


def expected_deals_for_level(level: int) -> list[str]:
    sets = LEVEL_CONFIG[level]["sets"]
    deals = []
    for s in sets:
        count = 36 if s == "A" else 30
        for n in range(1, count + 1):
            deals.append(f"{s}-{n}")
    return deals


EXTRACT_STEP_JS = r"""(() => {
    const rev = document.querySelector('deal-review-screen');
    if (!rev) return null;
    const panels = Array.from(rev.querySelectorAll('hand-diagram-panel'));
    if (panels.length < 4) return null;

    const titleEl = document.querySelector('deal-popup .titleClass');
    const title = titleEl ? titleEl.innerText.trim() : '';

    // Hands: S, W, N, E
    const seats = ['S', 'W', 'N', 'E'];
    const hands = {};
    const highlighted = {};
    let totalCards = 0;
    panels.forEach((p, idx) => {
        const seat = seats[idx] || ('P' + idx);
        const suitEls = Array.from(p.querySelectorAll('.suitPanelClass'));
        const suitNames = ['C', 'D', 'H', 'S'];
        const suitMap = {};
        const hlMap = {};
        suitEls.forEach((sEl, sIdx) => {
            const sName = suitNames[sIdx];
            const cards = Array.from(sEl.querySelectorAll('.handDiagramCardClass'));
            const ranks = cards.map(c => c.innerText.trim()).filter(Boolean);
            suitMap[sName] = ranks;
            totalCards += ranks.length;
            const hlCards = cards.filter(c => {
                const bg = c.style.backgroundColor || '';
                return bg !== '' && bg !== 'transparent' && bg !== 'rgb(255, 255, 255)';
            }).map(c => c.innerText.trim()).filter(Boolean);
            if (hlCards.length) hlMap[sName] = hlCards;
        });
        hands[seat] = suitMap;
        if (Object.keys(hlMap).length) highlighted[seat] = hlMap;
    });

    // Current trick cards
    const trickEls = Array.from(rev.querySelectorAll('hand-diagram-current-trick-card .handDiagramCurrentTrickClass'));
    const trickCards = {};
    trickEls.forEach((tEl, idx) => {
        const seat = seats[idx];
        if (tEl.style.display !== 'none' && tEl.innerText.trim()) {
            trickCards[seat] = tEl.innerText.trim().replace(/\s+/g, '');
        }
    });

    // Auction, Dealer, Vulnerability
    const auctionBox = rev.querySelector('auction-box');
    let dealer = 'S';
    let vulnerability = 'None';
    const auctionCalls = [];
    if (auctionBox) {
        const headerOrder = ['W', 'N', 'E', 'S'];
        const headerCells = Array.from(auctionBox.querySelectorAll('auction-box-header-cell .auction-box-header-cell'));
        const vulSeats = [];
        headerCells.forEach((hc, idx) => {
            const bg = hc.style.backgroundColor || '';
            if (bg.includes('203') || bg.includes('255, 0, 0') || bg.includes('red')) {
                vulSeats.push(headerOrder[idx]);
            }
        });
        const nsVul = vulSeats.includes('N') || vulSeats.includes('S');
        const ewVul = vulSeats.includes('E') || vulSeats.includes('W');
        if (nsVul && ewVul) vulnerability = 'Both';
        else if (nsVul) vulnerability = 'NS';
        else if (ewVul) vulnerability = 'EW';

        const rows = Array.from(auctionBox.querySelectorAll('.auction-row'));
        if (rows.length > 0) {
            const firstRowChildren = Array.from(rows[0].children);
            let blankCount = 0;
            for (const ch of firstRowChildren) {
                if (ch.tagName.toLowerCase() !== 'auction-box-cell') blankCount++;
                else break;
            }
            dealer = headerOrder[blankCount % 4] || 'S';
        }
        rows.forEach(r => {
            Array.from(r.querySelectorAll('auction-box-cell')).forEach(c => {
                const callText = c.innerText.trim().replace(/\s+/g, '');
                if (callText) auctionCalls.push(callText);
            });
        });
    }

    // Contract & tricks
    const tp = rev.querySelector('tricks-panel');
    const tpLabels = tp ? Array.from(tp.querySelectorAll('.tricksPanelTricksLabelClass')).map(l => l.innerText.trim()) : [];
    const contractEl = tp ? tp.querySelector('auction-box-cell') : null;
    const contract = contractEl ? contractEl.innerText.trim().replace(/\s+/g, '') : '';

    // Commentary
    const movieEl = rev.querySelector('.movieClass');
    const commentary = movieEl ? movieEl.innerText.trim() : '';

    // Next button status
    const nextBtn = Array.from(rev.querySelectorAll('button.bmButtonClass')).find(b => b.innerText.trim() === 'Next');
    const nextDisabled = !nextBtn || nextBtn.disabled || nextBtn.getAttribute('disabled') !== null;

    return {
        title,
        total_cards: totalCards,
        contract,
        dealer,
        vulnerability,
        auction: auctionCalls,
        tricks_labels: tpLabels,
        hands,
        highlighted,
        trick_cards: trickCards,
        commentary,
        next_disabled: nextDisabled
    };
})()"""


def normalize_rank(r: str) -> str:
    return "T" if r == "10" else r


def normalize_card(card_str: str) -> str:
    for sym, letter in SUIT_SYMBOLS.items():
        if sym in card_str:
            rank = card_str.replace(sym, "").strip()
            return f"{letter}{normalize_rank(rank)}"
    return card_str


def normalize_call(call_str: str) -> str:
    for sym, letter in SUIT_SYMBOLS.items():
        call_str = call_str.replace(sym, letter)
    return call_str


def hands_to_pbn(hands: dict[str, dict[str, list[str]]]) -> str:
    parts = []
    for seat in ["S", "W", "N", "E"]:
        seat_hand = hands.get(seat, {})
        suit_strs = []
        for suit in ["S", "H", "D", "C"]:
            ranks = [normalize_rank(r) for r in seat_hand.get(suit, [])]
            suit_strs.append("".join(ranks))
        parts.append(".".join(suit_strs))
    return "S:" + " ".join(parts)


def parse_contract_tricks_needed(contract: str) -> int | None:
    m = re.match(r"^([1-7])(C|D|H|S|NT)", normalize_call(contract))
    if not m:
        return None
    return int(m.group(1)) + 6


def build_deal_record(
    level: int, level_name: str, deal_id: str, raw_steps: list[dict]
) -> dict:
    # Find the first step that has all 52 cards (including any card already in trick_cards)
    first = next(
        (
            s
            for s in raw_steps
            if s.get("total_cards", 0) + len(s.get("trick_cards", {})) == 52
        ),
        raw_steps[0],
    )
    initial_hands = {
        seat: {suit: list(ranks) for suit, ranks in suit_map.items()}
        for seat, suit_map in first["hands"].items()
    }
    if first.get("total_cards", 0) < 52 and first.get("trick_cards"):
        for seat, c_str in first["trick_cards"].items():
            norm_c = normalize_card(c_str)
            if len(norm_c) >= 2:
                s_let, r_let = norm_c[0], norm_c[1:]
                if r_let not in [
                    normalize_rank(x)
                    for x in initial_hands.get(seat, {}).get(s_let, [])
                ]:
                    initial_hands.setdefault(seat, {}).setdefault(s_let, []).append(
                        r_let
                    )

    # Fix two upstream BBO .lin md| typos in BBO's database:
    # 1) Level 2 D-23: West's diamond '10' was omitted in md| (giving W 12 cards and E 14 cards)
    if level == 2 and deal_id == "D-23":
        if not initial_hands.get("W", {}).get("D") and "10" in initial_hands.get(
            "E", {}
        ).get("D", []):
            initial_hands["W"]["D"] = ["10"]
            initial_hands["E"]["D"] = [r for r in initial_hands["E"]["D"] if r != "10"]
    # 2) Level 4 A-10: South's spade '32' was omitted in solution movie md| (present on main table)
    if level == 4 and deal_id == "A-10":
        if not initial_hands.get("S", {}).get("S"):
            initial_hands["S"]["S"] = ["3", "2"]
            initial_hands["E"] = {
                "S": ["J", "7", "6"],
                "H": ["10", "9", "8", "7"],
                "D": ["5", "4"],
                "C": ["Q", "J", "10", "9"],
            }

    deal_pbn = hands_to_pbn(initial_hands)
    contract = normalize_call(first["contract"])
    vulnerability = first.get("vulnerability", "None")
    auction = [normalize_call(c) for c in first.get("auction", [])]

    # Derive exact dealer from auction & contract (Declarer is always South)
    seat_order = ["W", "N", "E", "S"]
    base_contract = contract.replace("x", "").replace("X", "")
    c_strain = re.sub(r"^[1-7]", "", base_contract)
    non_pass_idxs = [
        i for i, b in enumerate(auction) if b not in ("Pass", "Dbl", "Rdbl")
    ]
    if non_pass_idxs:
        last_bid_idx = non_pass_idxs[-1]
        ns_strain_idxs = [
            i
            for i in non_pass_idxs
            if (last_bid_idx - i) % 2 == 0
            and re.sub(r"^[1-7]", "", auction[i]) == c_strain
        ]
        dealer = (
            seat_order[(3 - ns_strain_idxs[0]) % 4]
            if ns_strain_idxs
            else first.get("dealer", "S")
        )
    else:
        dealer = first.get("dealer", "S")

    raw_paragraphs: list[str] = []
    for st in raw_steps:
        txt = " ".join(st.get("commentary", "").split())
        if not txt:
            continue
        if raw_paragraphs and txt.startswith(raw_paragraphs[-1]):
            raw_paragraphs[-1] = txt
        elif not raw_paragraphs or txt != raw_paragraphs[-1]:
            raw_paragraphs.append(txt)

    paragraphs: list[str] = []
    for p in raw_paragraphs:
        if (
            paragraphs
            and p[0].islower()
            and not paragraphs[-1].endswith((".", "!", "?", '"', "'", ")"))
        ):
            paragraphs[-1] = paragraphs[-1] + " " + p
        else:
            paragraphs.append(p)

    solution_steps = []
    for st in raw_steps:
        decl_tricks = (
            int(st["tricks_labels"][1])
            if len(st.get("tricks_labels", [])) > 2 and st["tricks_labels"][1].isdigit()
            else 0
        )
        def_tricks = (
            int(st["tricks_labels"][2])
            if len(st.get("tricks_labels", [])) > 2 and st["tricks_labels"][2].isdigit()
            else 0
        )
        hl_norm = {
            seat: {
                suit: [normalize_rank(r) for r in ranks]
                for suit, ranks in suit_map.items()
            }
            for seat, suit_map in st.get("highlighted", {}).items()
        }
        step_pbn = hands_to_pbn(st["hands"])
        if level == 2 and deal_id == "D-23":
            hp = step_pbn[2:].split(" ")
            w_s, e_s = hp[1].split("."), hp[3].split(".")
            if w_s[2] == "" and "T" in e_s[2]:
                w_s[2] = "T"
                e_s[2] = e_s[2].replace("T", "")
                hp[1], hp[3] = ".".join(w_s), ".".join(e_s)
                step_pbn = "S:" + " ".join(hp)
        elif level == 4 and deal_id == "A-10":
            if step_pbn.startswith("S:.AQ2.AJT98.AK2") and step_pbn.endswith("..."):
                hp = step_pbn[2:].split(" ")
                hp[0] = "32.AQ2.AJT98.AK2"
                hp[3] = "J76.T987.54.QJT9"
                step_pbn = "S:" + " ".join(hp)

        cand = {
            "step": len(solution_steps),
            "hands_pbn": step_pbn,
            "trick_cards": {
                seat: normalize_card(c) for seat, c in st.get("trick_cards", {}).items()
            },
            "declarer_tricks": decl_tricks,
            "defense_tricks": def_tricks,
            "highlighted": hl_norm,
            "commentary": " ".join(st.get("commentary", "").split()),
        }
        if solution_steps:
            prev = solution_steps[-1]
            if (
                prev["hands_pbn"],
                prev["trick_cards"],
                prev["commentary"],
                prev["highlighted"],
                prev["declarer_tricks"],
                prev["defense_tricks"],
            ) == (
                cand["hands_pbn"],
                cand["trick_cards"],
                cand["commentary"],
                cand["highlighted"],
                cand["declarer_tricks"],
                cand["defense_tricks"],
            ):
                continue
        solution_steps.append(cand)

    play_sequence: list[dict] = []
    prev_trick: dict[str, str] = {}
    opening_lead = ""
    for st in solution_steps:
        tc = st.get("trick_cards", {})
        for seat, card in tc.items():
            if prev_trick.get(seat) != card:
                play_sequence.append({"step": st["step"], "seat": seat, "card": card})
                if not opening_lead and seat == "W":
                    opening_lead = card
        prev_trick = tc
    if not opening_lead and play_sequence:
        opening_lead = play_sequence[0]["card"]
    if not opening_lead and level == 1 and deal_id == "A-17":
        opening_lead = "SJ"

    return {
        "title": f"Level {level} ({level_name}) - {deal_id}",
        "level": level,
        "level_name": level_name,
        "deal_id": deal_id,
        "deal_pbn": deal_pbn,
        "contract": contract,
        "declarer": "S",
        "dealer": dealer,
        "vulnerability": vulnerability,
        "auction": auction,
        "opening_lead": opening_lead,
        "par_tricks": parse_contract_tricks_needed(contract),
        "notes": "\n\n".join(paragraphs),
        "commentary_paragraphs": paragraphs,
        "play_sequence": play_sequence,
        "solution_steps": solution_steps,
    }


class CDPBrowser:
    def __init__(self, port: int):
        self.port = port
        self.tmp_dir = tempfile.mkdtemp(prefix=f"bbo_chrome_{port}_")
        self.proc: subprocess.Popen | None = None
        self.ws: websocket.WebSocket | None = None
        self.msg_id = 0

    def start(self) -> None:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.proc = subprocess.Popen(
            [
                chrome_path,
                "--headless=new",
                "--window-size=1280,900",
                "--disable-gpu",
                "--disable-extensions",
                "--no-first-run",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                f"--remote-debugging-port={self.port}",
                "--remote-allow-origins=*",
                "--ignore-certificate-errors",
                f"--user-data-dir={self.tmp_dir}",
                "https://www.bridgebase.com/v3/?bridgemaster=y",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait for debugger endpoint and page tab
        ws_url = None
        for _ in range(30):
            time.sleep(1)
            try:
                tabs = json.loads(
                    urllib.request.urlopen(
                        f"http://127.0.0.1:{self.port}/json", timeout=3
                    )
                    .read()
                    .decode()
                )
                page_tabs = [t for t in tabs if t.get("type") == "page"]
                if page_tabs:
                    ws_url = page_tabs[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                pass
        if not ws_url:
            raise RuntimeError(
                f"Port {self.port}: Failed to connect to Chrome debugger"
            )

        self.ws = websocket.create_connection(ws_url, timeout=20)

        # Wait for Bridge Master skill selection screen
        for _ in range(45):
            cnt = self.eval(
                'document.querySelectorAll("button.skillButtonClass").length'
            )
            if cnt and cnt >= 5:
                return
            time.sleep(1)
        raise RuntimeError(
            f"Port {self.port}: Timed out waiting for Bridge Master menu"
        )

    def eval(self, expr: str):
        assert self.ws is not None
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(
            json.dumps(
                {
                    "id": mid,
                    "method": "Runtime.evaluate",
                    "params": {"expression": expr, "returnByValue": True},
                }
            )
        )
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                res = msg.get("result", {})
                if "exceptionDetails" in res:
                    raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
                return res.get("result", {}).get("value")

    def stop(self) -> None:
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=3)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None
        shutil.rmtree(self.tmp_dir, ignore_errors=True)


def navigate_and_scrape_deal(
    browser: CDPBrowser, level: int, level_name: str, deal_id: str
) -> dict:
    # Close solution modal if open
    browser.eval(
        r"""(() => {
        const closeBtn = document.querySelector('deal-popup button.modal-close-button');
        if (closeBtn) closeBtn.click();
    })()"""
    )
    time.sleep(0.2)

    # Check if we are already on the main table or on the home/select popup
    on_popup = browser.eval(
        'document.querySelectorAll("button.skillButtonClass").length >= 5'
    )
    table_ready = False
    if not on_popup:
        # Try clicking 'Next deal' directly on the table first for fast sequential progression
        clicked_next_deal = browser.eval(
            r"""(() => {
            const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.trim().toLowerCase() === 'next deal' && x.offsetParent !== null && !x.disabled);
            if (b) { b.click(); return true; }
            return false;
        })()"""
        )
        if clicked_next_deal:
            for _ in range(18):
                time.sleep(0.15)
                matched = browser.eval(
                    rf"""(() => {{
                    const p = document.querySelector('deal-viewer:not([movieviewer="true"]) bridge-master-panel .detailsClass');
                    const tag = p ? p.innerText.trim().replace(/\s+/g, ' ') : '';
                    return tag.includes('Level {level}') && tag.endsWith(' {deal_id}');
                }})()"""
                )
                if matched:
                    table_ready = True
                    break

    if not table_ready:
        if not on_popup:
            clicked_select = browser.eval(
                r"""(() => {
                const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.trim().toLowerCase() === 'select deal' && x.offsetParent !== null);
                if (b) { b.click(); return true; }
                return false;
            })()"""
            )
            if clicked_select:
                for _ in range(30):
                    if browser.eval(
                        'document.querySelectorAll("button.skillButtonClass").length >= 5'
                    ):
                        break
                    time.sleep(0.15)

        # Click the level button (0-indexed) and wait until its parent shows the yellow active highlight
        browser.eval(
            f'document.querySelectorAll("button.skillButtonClass")[{level - 1}].click()'
        )
        for _ in range(30):
            lvl_active = browser.eval(
                f'(() => {{ const b = document.querySelectorAll("button.skillButtonClass")[{level - 1}]; return !!(b && b.parentElement && (b.parentElement.style.backgroundColor || "").includes("255, 206, 0")); }})()'
            )
            if lvl_active:
                break
            time.sleep(0.15)
        time.sleep(0.5)

        for _ in range(25):
            has_deal = browser.eval(
                f'!!Array.from(document.querySelectorAll("div.dealDivClass")).find(d => d.innerText.trim() === "{deal_id}")'
            )
            if has_deal:
                break
            time.sleep(0.15)

        # Click the deal_id item
        clicked_deal = browser.eval(
            f'(() => {{ const d = Array.from(document.querySelectorAll("div.dealDivClass")).find(x => x.innerText.trim() === "{deal_id}"); if (d) {{ d.scrollIntoView({{block: "center"}}); d.click(); return true; }} return false; }})()'
        )
        if not clicked_deal:
            raise RuntimeError(f"Could not find deal {deal_id} in Level {level} list")

    # Wait for main table to show Level {level} and {deal_id} and Show solution button
    expected_tag = f"Level {level} {deal_id}"
    for _ in range(60):
        ready = browser.eval(
            rf"""(() => {{
            const p = document.querySelector('deal-viewer:not([movieviewer="true"]) bridge-master-panel .detailsClass');
            const tag = p ? p.innerText.trim().replace(/\s+/g, ' ') : '';
            const solBtn = Array.from(document.querySelectorAll('button')).find(x => x.innerText.trim().toLowerCase().includes('solution') && x.offsetParent !== null);
            return tag.includes('Level {level}') && tag.endsWith(' {deal_id}') && !!solBtn;
        }})()"""
        )
        if ready:
            break
        time.sleep(0.15)
    else:
        raise RuntimeError(f"Timed out waiting for table {expected_tag}")

    # Give BBO server a brief moment to finish dealing the board on the table
    time.sleep(0.35)

    # Click Show solution (with in-page re-click if solution movie takes a moment)
    expected_title = f"Bridge Master - Level {level} - {deal_id}"
    st = None
    for sol_try in range(3):
        browser.eval(
            r"""(() => {
            const closeBtn = document.querySelector('deal-popup button.modal-close-button');
            if (closeBtn) closeBtn.click();
        })()"""
        )
        if sol_try > 0:
            time.sleep(0.5)
        browser.eval(
            "Array.from(document.querySelectorAll('button')).find(x => x.innerText.trim().toLowerCase().includes('solution') && x.offsetParent !== null).click()"
        )
        matched_modal = False
        for _ in range(35):
            st = browser.eval(EXTRACT_STEP_JS)
            if (
                st
                and st.get("title") == expected_title
                and (
                    (st.get("total_cards", 0) + len(st.get("trick_cards", {})) == 52)
                    or (
                        level == 4
                        and deal_id == "A-10"
                        and st.get("total_cards", 0) >= 35
                    )
                )
                and st.get("contract")
            ):
                matched_modal = True
                break
            time.sleep(0.15)
        if matched_modal:
            break
    else:
        raise RuntimeError(
            f"Timed out waiting for solution modal '{expected_title}' (got {st.get('title') if st else None})"
        )

    # Step through Next until next_disabled is True
    raw_steps = []
    for _ in range(250):
        st = browser.eval(EXTRACT_STEP_JS)
        if not st:
            raise RuntimeError(
                f"Solution viewer disappeared mid-deal on {expected_title}"
            )
        raw_steps.append(st)
        if st["next_disabled"]:
            break

        prev_sig = json.dumps(
            [
                st["hands"],
                st["trick_cards"],
                st["commentary"],
                st["highlighted"],
                st["next_disabled"],
            ]
        )
        browser.eval(
            "Array.from(document.querySelectorAll('deal-review-screen button.bmButtonClass')).find(b => b.innerText.trim() === 'Next').click()"
        )
        for _ in range(25):
            time.sleep(0.07)
            st2 = browser.eval(EXTRACT_STEP_JS)
            if st2:
                sig2 = json.dumps(
                    [
                        st2["hands"],
                        st2["trick_cards"],
                        st2["commentary"],
                        st2["highlighted"],
                        st2["next_disabled"],
                    ]
                )
                if sig2 != prev_sig:
                    break

    record = build_deal_record(level, level_name, deal_id, raw_steps)
    issues = validate_deal_pbn(record["deal_pbn"], record["title"])
    if issues:
        raise RuntimeError(f"Validation failed for {record['title']}: {issues}")
    return record


def deal_file_path(level: int, deal_id: str) -> Path:
    folder = LEVEL_CONFIG[level]["folder"]
    set_letter = deal_id.split("-")[0]
    return BASE_OUT_DIR / folder / set_letter / f"{deal_id}.json"


def scrape_level_worker(level: int, port: int) -> tuple[int, int]:
    level_info = LEVEL_CONFIG[level]
    level_name = level_info["name"]
    deals = expected_deals_for_level(level)

    todo_deals = []
    for d_id in deals:
        cp_path = deal_file_path(level, d_id)
        if cp_path.exists():
            try:
                data = json.loads(cp_path.read_text(encoding="utf-8"))
                if not validate_deal_pbn(
                    data.get("deal_pbn", ""), data.get("title", "")
                ):
                    continue
            except Exception:
                pass
        todo_deals.append(d_id)

    done_count = len(deals) - len(todo_deals)
    log(
        f"[Level {level} - {level_name}] Starting worker on port {port}: {done_count}/{len(deals)} already cached, {len(todo_deals)} to scrape."
    )
    if not todo_deals:
        return len(deals), len(deals)

    browser: CDPBrowser | None = None
    try:
        for d_id in todo_deals:
            cp_path = deal_file_path(level, d_id)
            cp_path.parent.mkdir(parents=True, exist_ok=True)
            for attempt in range(1, 4):
                try:
                    if browser is None:
                        browser = CDPBrowser(port)
                        browser.start()
                    t0 = time.time()
                    rec = navigate_and_scrape_deal(browser, level, level_name, d_id)
                    cp_path.write_text(
                        json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    done_count += 1
                    dt = time.time() - t0
                    if (
                        done_count % 5 == 0
                        or done_count == len(deals)
                        or d_id.endswith("-1")
                    ):
                        log(
                            f"[Level {level} - {level_name}] {done_count}/{len(deals)} ({d_id}) scraped in {dt:.1f}s "
                            f"[{rec['contract']} by S, lead {rec['opening_lead']}, {len(rec['solution_steps'])} steps]"
                        )
                    break
                except Exception as e:
                    log(
                        f"[Level {level} - {level_name}] Warn on {d_id} (attempt {attempt}/3): {e}"
                    )
                    if browser is not None:
                        browser.stop()
                        browser = None
                    time.sleep(2)
            else:
                log(
                    f"[Level {level} - {level_name}] ERROR: Failed {d_id} after 3 attempts"
                )
    finally:
        if browser is not None:
            browser.stop()

    return done_count, len(deals)


def write_master_index() -> None:
    summary = {
        "source": "Bridge Base Online - Bridge Master (Fred Gitelman)",
        "url": "https://www.bridgebase.com/v3/?bridgemaster=y",
        "total_deals": 0,
        "levels": [],
    }
    total_scraped = 0
    for lvl, info in LEVEL_CONFIG.items():
        set_counts = {}
        lvl_total = 0
        for s in info["sets"]:
            set_dir = BASE_OUT_DIR / info["folder"] / s
            cnt = len(list(set_dir.glob("*.json"))) if set_dir.exists() else 0
            set_counts[s] = cnt
            lvl_total += cnt
        total_scraped += lvl_total
        summary["levels"].append(
            {
                "level": lvl,
                "level_name": info["name"],
                "folder": info["folder"],
                "total_deals": lvl_total,
                "sets": set_counts,
            }
        )
    summary["total_deals"] = total_scraped
    BASE_OUT_DIR.mkdir(parents=True, exist_ok=True)
    (BASE_OUT_DIR / "index.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--levels", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()

    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {
            pool.submit(scrape_level_worker, lvl, 9230 + lvl): lvl
            for lvl in args.levels
        }
        for fut in concurrent.futures.as_completed(futs):
            lvl = futs[fut]
            done, total = fut.result()
            log(
                f"=== COMPLETED Level {lvl} ({LEVEL_CONFIG[lvl]['name']}): {done}/{total} deals ==="
            )
            write_master_index()

    write_master_index()
    log(f"All requested levels finished in {time.time() - t0:.1f}s.")


if __name__ == "__main__":
    main()
