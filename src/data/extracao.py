import os
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src import config as C


def csv_to_parquet(csv_path, out_path, chunksize=500_000):
    size = os.path.getsize(csv_path)
    writer = None
    total = 0
    t0 = time.time()

    with open(csv_path, "rb") as f:
        for chunk in pd.read_csv(
            f,
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
            total += len(chunk)
            pct = min(f.tell() / size * 100, 100)
            print(f"\r{pct:5.1f}% | {total:,} linhas | {time.time() - t0:.0f}s", end="", flush=True)

    writer.close()
    print(f"\r100.0% | {total:,} linhas | {(time.time() - t0) / 60:.1f} min - concluído")
    return out_path
