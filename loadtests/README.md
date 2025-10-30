
# k6 Load Tests (K072)

Run (fixtures):
```
k6 run -e GOLEX_API="https://your-api" -e VUS=50 -e DURATION=1m fixtures.js
```

Search:
```
k6 run -e GOLEX_API="https://your-api" search.js
```

Predictions:
```
k6 run -e GOLEX_API="https://your-api" -e FIXTURE_ID=12345 predictions.js
```

Live (poll):
```
k6 run -e GOLEX_API="https://your-api" live_poll.js
```
