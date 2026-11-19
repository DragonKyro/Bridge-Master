// Routes: home, a level's deals, a deal at the table (with its solution on top).

import { useEffect } from 'react';
import { usePrefs } from '@/store/prefsStore';
import { LevelPage } from './pages/LevelPage';
import { Home } from './pages/Home';
import { useRoute } from './router';
import { StarDefs } from './shared/Stars';
import { TablePage } from './table/TablePage';

export function App() {
  const route = useRoute();
  const fourColor = usePrefs((s) => s.fourColor);
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [route.name, route.name === 'level' ? route.level : 0]);

  return (
    <div className={`app${fourColor ? '' : ' suits-two'}`}>
      <StarDefs />
      {route.name === 'home' && <Home />}
      {route.name === 'level' && <LevelPage key={route.level} level={route.level} />}
      {route.name === 'deal' && <TablePage id={route.id} solution={route.solution} />}
    </div>
  );
}
