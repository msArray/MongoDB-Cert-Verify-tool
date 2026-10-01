# MongoDB-Cert-Verify-tool

## Useage

set `.env` file and set MongoDB URI

run this


```
uv run pyi-makespec --onefile --windowed --name main `
  --add-data "app/styles/main.qss:app/styles" `
  --add-data ".env:." `
  main.py
uv run pyarmor gen --pack main.spec -r main.py
```

to bundle exe file