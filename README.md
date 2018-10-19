# Build queue manager

statuses:

* WAITING not running yet
* BUILDING currently building on sr.ht
* FAILED build failed on sr.ht
* SUPERSEDED a job for a newer version of the package has been submitted
* DONE everything build successfully

## API

### Submitting task to queue
```http
POST /api/task-submit
Content-Type: application/json
X-Secret: very-secret-token

{
    "package": "linux-postmarketos-qcom",
    "pkgver": "4.18.0",
    "pkgrel": 4,
    "commit": "123456788abcdef",
    "arch": "armhf",
    "branch": "master"
}
```

Response

```http
Content-Type: application/json

{
    "status": "ok"
}
```