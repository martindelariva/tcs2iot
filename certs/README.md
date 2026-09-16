# Device certificates

Drop your AWS IoT Thing certificates here (this folder is git-ignored):

- `device.pem.crt`     — the device certificate
- `private.pem.key`    — the private key
- `AmazonRootCA1.pem`  — Amazon Root CA 1

Download the Root CA:

    curl -o AmazonRootCA1.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem

The `processor` service mounts this folder read-only at `/certs`.
Until `IOT_ENDPOINT` is set in `.env`, the processor runs in dry-run mode
and does not need these files.
