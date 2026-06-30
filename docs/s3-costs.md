# S3 Cost Notes

This stack creates an S3 bucket named `files.pacd.edu`.

## Current Bucket Configuration

The bucket is configured with:

- private public-access blocking
- S3-managed encryption
- HTTPS-only access
- `RemovalPolicy.DESTROY`
- `auto_delete_objects=True`

This means CloudFormation can delete the bucket when the bucket resource is removed from the stack or the stack is destroyed. `auto_delete_objects=True` adds a CDK custom resource that empties the bucket before deletion.

## Expected Cost for an Empty Bucket

An empty S3 bucket has no meaningful storage cost.

```text
Bucket exists, no objects: about $0
```

## What Creates S3 Cost

S3 is pay as you go. Main cost drivers are:

- object storage
- PUT, COPY, POST, LIST, and GET requests
- data transfer out
- replication
- lifecycle transitions
- optional analytics, inventory, logging, or monitoring features

For S3 Standard in `us-east-1`, common reference prices are:

```text
Storage: about $0.023 per GB-month
PUT/COPY/POST/LIST requests: about $0.005 per 1,000 requests
GET requests: about $0.0004 per 1,000 requests
DELETE requests: free
```

Examples:

```text
1 GB stored for 1 month: about $0.023
10 GB stored for 1 month: about $0.23
100 GB stored for 1 month: about $2.30
```

## Deletion Behavior

The bucket intentionally does not use a retain policy.

```python
removal_policy=RemovalPolicy.DESTROY
auto_delete_objects=True
```

If the bucket has objects, `auto_delete_objects=True` lets CDK empty the bucket before deleting it. Without this, S3 bucket deletion can fail when the bucket is not empty.

Pricing reference: <https://aws.amazon.com/s3/pricing/>
