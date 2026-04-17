# Operations

Running the pipeline, environment variables, monitoring, and troubleshooting.

---

## 1. Local Development

```bash
make install      # uv sync --extra dev
make test         # uv run pytest
make lint         # uv run ruff check src/ tests/
make lint-fix     # uv run ruff check --fix src/ tests/
make run          # process data/sample_input.tsv, output to current dir
```

Custom input/output:

```bash
uv run python -m search_keyword_revenue.cli path/to/data.tsv --output-dir /tmp/output/
```

### Dev Flow

```
1. git checkout -b feature/my-change
2. Edit src/search_keyword_revenue/
3. make test && make lint
4. git push origin feature/my-change (CI runs)
5. Open PR -> merge to main (CI + CD (sam deploy))
```

---

## 2. Running the Pipeline

### S3 Trigger (Production)

Upload a TSV to the `raw/` prefix. Lambda fires automatically within seconds.

```bash
aws s3 cp data/sample_input.tsv s3://skr-raw-dev-${ACCOUNT_ID}/raw/sample_input.tsv

# Check for output
aws s3 ls s3://skr-processed-dev-${ACCOUNT_ID}/processed/
```

### Local CLI

```bash
uv run python -m search_keyword_revenue.cli data/sample_input.tsv
```

---

## 3. Monitoring

### Tail Lambda Logs

```bash
aws logs tail /aws/lambda/search-keyword-revenue-dev --follow
```

### Filter for Errors

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/search-keyword-revenue-dev \
  --filter-pattern "ERROR"
```

### Check S3 Output

```bash
aws s3 ls s3://skr-processed-dev-${ACCOUNT_ID}/processed/
```

---

## 4. Troubleshooting

### Lambda not triggering after S3 upload

Confirm the file is under the `raw/` prefix — the bucket root does not trigger Lambda:

```bash
aws s3 ls s3://skr-raw-dev-${ACCOUNT_ID}/raw/
```

Check the S3 event notification:

```bash
aws s3api get-bucket-notification-configuration --bucket skr-raw-dev-${ACCOUNT_ID}
# Should contain a LambdaFunctionConfigurations entry with "Prefix": "raw/"
```
