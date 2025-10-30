
import http from 'k6/http';
import { sleep, check } from 'k6';
import { BASE, HEADERS, options } from './common.js';
export { options };

export default function () {
  const q = ['real', 'barca', 'uni', 'liv', 'bay'].Math ? 'real' : 'real'; // simple
  const r = http.get(`${BASE}/search?q=real&fuzzy=1`, { headers: HEADERS });
  check(r, { '200': (res) => res.status === 200 });
  sleep(1);
}
