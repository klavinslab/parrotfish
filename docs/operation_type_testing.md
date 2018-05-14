# Operation Type Testing

Parrotfish allows you to test your Operation Types locally with an Aquarium Docker container.

## Docker Setup

Before you can run tests, you must install Docker and build the Aquarium Docker container. Please follow the instructions in the [aquadocked](https://github.com/klavinslab/aquadocked) repository.

_Parrotfish expects the container to be tagged as 'aq'. This will be the case if you follow the instructions correctly._

## Testing Setup

Notice that, upon `pfish fetch <category>`, a /testing folder is generated and is populated with `data.json`. Please consult the [Test Data Format](./test_data_format.md) documentation for information about this file.

## Running Tests

Parrotfish currently supports testing one Operation Type at a time. This takes the form

```bash
pfish test <category> <protocol_name>
```

We recommend that you set the `--reset` option when you run `pfish test`, as that will kill any running Aquarium container and start a new one before the test is run. However, starting the container can take some time, so omit `--reset` for faster tests.

To conveniently start and stop the container, these methods are available:

```bash
pfish start-container
```

and

```bash
pfish stop-container
```
