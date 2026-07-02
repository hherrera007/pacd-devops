# CSV Upload Demo

This example uses a local HTML page to send a CSV file to the public Lambda Function URL.

## Requirement

After deploying the stack, copy the output value:

```text
CsvUploadFunctionUrl
```

Then replace this value in `csv-upload-demo.html`:

```js
const lambdaUrl = "https://REPLACE_WITH_LAMBDA_FUNCTION_URL/";
```

## CSV Structure

The file must be a comma-separated CSV and must have exactly these columns:

```text
fecha,producto,categoria,cantidad,precio_unitario,cliente
```

Example:

```csv
fecha,producto,categoria,cantidad,precio_unitario,cliente
2026-07-01,Laptop,Tecnologia,1,1200.00,Juan Perez
```

Rules:

- `fecha` must use `YYYY-MM-DD` format
- `producto` must not be empty
- `categoria` must not be empty
- `cantidad` must be greater than zero
- `precio_unitario` must be greater than zero
- `cliente` must not be empty

## Usage

Open `csv-upload-demo.html` in the browser, select the CSV file, and click `Subir archivo`.

The page sends the file to the Lambda Function URL. The Lambda stores the file in:

```text
s3://files.pacd.edu/inbound/
```

After that, the S3 notification triggers the Lambda that processes the CSV.

If you receive `Forbidden`, redeploy the stack to apply the public Lambda Function URL permissions.
