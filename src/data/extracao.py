import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src import config as C

def csv_to_parquet(csv_path, out_path, chunksize=500_000):
    writer = None
    for chunk in pd.read_csv(
        csv_path,
        sep=C.CSV_SEP,
        usecols=C.COLS,
        chunksize=chunksize,
        encoding=C.CSV_ENCODING,
        low_memory=False,
    ):
        t = pa.Table.from_pandas(chunk.astype("string"), preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(out_path, t.schema, compression="zstd")
        writer.write_table(t)
    writer.close()
    return out_path
