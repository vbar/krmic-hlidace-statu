# krmic-hlidace-statu

These are single-purpose scripts - not only useless by themselves, but
even when integrated (or planned to be integrated) into a larger
pipeline, of interest only to people who 1) speak Czech, and 2) are
interested in Czech Open Data and/or public procurement.

www.hlidacstatu.cz indexes and curates data made available
(compulsorily and not very conveniently) by Czech public
administration - public contracts, companies servicing them,
politicians on their boards etc. Among other things, it publishes a
developer API (described at https://hlidacstatu.docs.apiary.io/ )
allowing registered 3rd parties to upload structured data they
consider relevant to the site's mission.

The data is modelled as a dataset - a sequence of JSON objects with a
mandatory "Id" attribute. Every dataset has a JSON schema, defined by
dataset's author. When one has some JSON data, the schema can be
produced semi-automatically by a JSON schema generator and
incorporated in the dataset description, quoting the schema JSON as a
single string value (as described in the documentation referenced
above). For presentation, the dataset description also requires a
couple of templates specifying how to format the JSON data as HTML,
also quoted when included.

The dataset-roundtrip.py script moves these structured values from the
dataset description into separate files and back, so that they can be
edited in their native format. What should be moved where is specified
by a "matrix" JSON file - basically the dataset description where the
quoted values were replaced by strings starting with '@' and
continuing with file names. It's the matrix's author responsibility to
use unique and valid names - the script just uses them as
specified. dataset-roundtrip.py can run in 2 modes: "pack" combines
matrix and the files named in it into the dataset description (which
can then be manually uploaded to hlidacstatu.cz) while "unpack" copies
values from the dataset description into files specified in the
matrix. All parameters of this script are specified on its command
line - for details, run it without any.

Individual dataset items can also be uploaded manually, but for
collections of useful size that's impractical, because each item must
be POSTed separately. The pusher.py script automates this cycle. For
configuration, it requires a config.json file in the current
directory. config.json has 2 mandatory settings: "token" for the API
access token, available from hlidacstatu.cz upon registration, and
"datasetId" for the uploaded dataset name, returned when it's
created. The "mode" setting specifies how to handle uploaded items
that already exist on the server: "rewrite" to replace them and
"merge" to combine them. The "sourceDir" setting specifies the
directory with files to upload; its value is "json" by default. Note
that to mark progress, contents of the "sourceDir" are destroyed after
succesfull upload - make sure it's not your only copy!

Files in the "json" directory represent dataset items to be uploaded -
every file must have the item's Id as a name, plus a ".json" extension
(e.g. "a1fa5ee3-d57a-4065-bde3-50d40a1ce269.json" for an item with Id
"a1fa5ee3-d57a-4065-bde3-50d40a1ce269"). The contents must be a JSON
object conforming to the dataset's schema, including the same Id
that's in the name of the file. pusher.py simply goes through the
"json" directory, POSTs the files, checks the API's return value and
either removes the uploaded file on success, or ends on error.
