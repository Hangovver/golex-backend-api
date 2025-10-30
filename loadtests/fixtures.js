
import http from 'k6/http';
import { sleep, check } from 'k6';
import { BASE, HEADERS, options } from './common.js';
export { options };

export default function () {
  const r = http.get(`${BASE}/leagues/39/fixtures?type=upcoming&limit=20`, { headers: HEADERS });
  check(r, { '200': (res) => res.status === 200 });
  sleep(1);
}
