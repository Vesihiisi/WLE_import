# WLE-import
Importing Swedish protected nature data to Wikidata.

## Harvest existing Wikidata items

**reserve_harvester.py** collects nature reserve items currently on Wikidata, based on a [Petscan search](https://petscan.wmflabs.org/?psid=914993), and matches them with Nature IDs from the source file. Articles that can't be matched are saved in separate files.

## Process and upload nature areas

**nature_importer.py** processes data from the csv files and uploads them to Wikidata.

```
python3 nature_importer.py --dataset nr --offset 100 --limit 10 --upload live
```

`dataset` -- either "nr" for nature reserves or "np" for national parks.

`offset` -- don't start from the beginning of the file, but with an offset of a number of rows.

`limit` -- only process a limited number of entries.

`table` -- create a preview table of results and save to file.

`upload` -- to upload the created claims to Wikidata. You can leave it out if you want to debug the NatureArea object processing. **By default** this will use the [Wikidata Sandbox](https://www.wikidata.org/wiki/Q4115189). Add `live` to work on actual live Wikidata items, assuming you're 100% positive you want to do that.