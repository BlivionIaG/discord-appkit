# Architecture

This tool manages Discord applications and assets, and writes the CI that syncs the resulting catalogs into another project.

```
apps/*.yaml + assets/*
        |
        v
appkit plan / apply
        |
        v
state/ids.lock.json
        |
        v
appkit emit --format <consumer> --out <dir>
```

`appkit ci init` writes that emit step into the consumer repository. FetchCord uses `--format fetchcord-testing` and `--out fetch_cord/resources`. The tool is not limited to that format.
