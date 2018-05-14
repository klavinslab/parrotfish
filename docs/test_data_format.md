# Test Data Format

Every time you `pfish fetch <category>` Parrotfish generates an `<operation_type>/testing/data.json` file that will be loaded into the Aquarium container when you test an Operation Type.
The data represented in this file should encompass _all_ of the database records involved in the given `OperationType`, including `Item`s, `Sample`s, `SampleType`s, `Operation`s, etc. Parrotfish generates data for three operations by default.

The following outline of the file structure uses _Rehydrate Primer_ as an example.

## Records

All `record`s are tagged for reference by other records described in the file.
These tags are used to establish relationships between records and are replaced with ids of the tagged record as the records are loaded into the Aquarium container.
An example `SampleType` and `Sample` definition:

```json
{
  "records": {
    "sample_types": [
      {
        "tag": "primer_st",
        "source": "sample_types/Primer.json"
      }
    ],
    "samples": [
      {
        "tag": "p_samp",
        "data": {
          "name": "Test P",
          "project": "trident",
          "sample_type": "primer_st",
          "user_id": 1
        }
      },
    ],
    ...
  },
  ...
}
```

### Items and Samples

Items and Samples are defined by a `tag` and `data`.
This data takes the form of the argument for
[`Model.load()` in Trident](https://github.com/klavinslab/trident/blob/master/docsrc/developer/api_notes.rst#working-with-models)
with one exception:
Any field that Trident expects to end with `_id` that points to a `tag` instead of to an integer will be replaced with the field name with `_id` appended, pointing to the id of the newly-created record.
An example follows:

```json
{
  "records": {
    "samples": [
      {
        "tag": "P_samp0",
        "data": {
          "name": "Test P 0",
          "project": "trident",
          "sample_type": "primer_st",
          "user_id": 1
        }
      },
      {
        "tag": "P_samp1",
        "data": {
          "name": "Test P 1",
          "project": "trident",
          "sample_type": "primer_st",
          "user_id": 1
        }
      },
      {
        "tag": "P_samp2",
        "data": {
          "name": "Test P 2",
          "project": "trident",
          "sample_type": "primer_st",
          "user_id": 1
        }
      }
    ],
    "items": [
      {
        "tag": "Primer_item0",
        "data": {
          "sample": "P_samp0",
          "object_type": "lyophilized primer_ot"
        }
      },
      {
        "tag": "Primer_item1",
        "data": {
          "sample": "P_samp1",
          "object_type": "lyophilized primer_ot"
        }
      },
      {
        "tag": "Primer_item2",
        "data": {
          "sample": "P_samp2",
          "object_type": "lyophilized primer_ot"
        }
      }
    ],
    ...
  },
  ...
}
```

### Object Types and Sample Types

Object Types and Sample Types are defined similarly to Items and Samples but differ in that they are provided by the Operation Type definition and are less typically modified for testing purposes.
Therefore, their `data` are housed in external files specified by `source`. This takes the following format:

```json
{
  "records": {
    "object_types": [
      {
        "tag": "lyophilized primer_ot",
        "source": "object_types/Lyophilized Primer.json"
      },
      {
        "tag": "primer aliquot_ot",
        "source": "object_types/Primer Aliquot.json"
      },
      {
        "tag": "primer stock_ot",
        "source": "object_types/Primer Stock.json"
      }
    ],
    "sample_types": [
      {
        "tag": "primer_st",
        "source": "sample_types/Primer.json"
      }
    ],
    ...
  },
  ...
}
```

### Operations

Operations are defined similarly to Items and Samples with the exception that their `data` encompasses further definitions for its inputs and outputs.
As this file is parsed, first the Operation is created, and then its inputs and outputs are created, where each `input` and `output` element takes the form of `data` expected by Trident.
An example follows:

```json
{
  "records": {
    "operations": [
      {
        "tag": "op0",
        "data": {
          "inputs": [
            {
              "name": "Primer",
              "sample": "P_samp0",
              "item": "Primer_item0"
            }
          ],
          "outputs": [
            {
              "name": "Primer Aliquot",
              "sample": "P_samp0"
            },
            {
              "name": "Primer Stock",
              "sample": "P_samp0"
            }
          ]
        }
      },
      {
        "tag": "op1",
        "data": {
          "inputs": [
            {
              "name": "Primer",
              "sample": "P_samp1",
              "item": "Primer_item1"
            }
          ],
          "outputs": [
            {
              "name": "Primer Aliquot",
              "sample": "P_samp1"
            },
            {
              "name": "Primer Stock",
              "sample": "P_samp1"
            }
          ]
        }
      },
      {
        "tag": "op2",
        "data": {
          "inputs": [
            {
              "name": "Primer",
              "sample": "P_samp2",
              "item": "Primer_item2"
            }
          ],
          "outputs": [
            {
              "name": "Primer Aliquot",
              "sample": "P_samp2"
            },
            {
              "name": "Primer Stock",
              "sample": "P_samp2"
            }
          ]
        }
      }
    ],
    ...
  },
  ...
}
```

## Plan

A single plan is generated for the test, and it is simply defined in this file by a list of tags of the operations to be created for this plan.
An example follows:

```json
{
  "plan": {
    "operations": [
      "op0",
      "op1",
      "op2"
    ]
  },
  ...
}
```
