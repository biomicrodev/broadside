# Notes
* in nextflow, absolute paths must be passed as `val` and not `path`, as `path` is a special process-aware location, and will resolve relative to the process dir.