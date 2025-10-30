
import http from 'k6/http';
import { sleep, check } from 'k6';
import { BASE, HEADERS, options } from './common.js';
export { options };

export default function () {
  const fid = __ENV.FIXTURE_ID || '1001';
  const url = `${BASE}/predictions/combined?fixtureId=${fid}&markets=KG+O2.5,1X+O1.5+KG`;
  const r = http.get(url, { headers: HEADERS });
  check(r, { '200': (res) => res.status === 200 });
  sleep(1);
}
