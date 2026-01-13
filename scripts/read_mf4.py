from typing import Sequence

from asammdf import MDF

mf4_paths: Sequence[str] = [
    # "/home/andrae/Dokumente/10_git/ares/examples/data/data_example_1.mf4",
    # "/home/andrae/Dokumente/10_git/ares/examples/data/data_example_2.mf4",
    "/home/andrae/Dokumente/10_git/ares/examples/data/data_example_3.mf4",
    "/home/andrae/Dokumente/10_git/ares/examples/output/data_3_5c64fdea_20260117190255.mf4",
]

all_data_dict: dict[str, dict[str, object]] = {}


for mf4_path in mf4_paths:
    data_dict: dict[str, object] = {}
    with MDF(mf4_path) as mdf:
        for group_index, group in enumerate(mdf.groups):
            for channel in group["channels"]:
                channel_name = channel.name
                key = f"group{group_index}:{channel_name}"
                try:
                    values = mdf.get(channel_name, group=group_index).samples
                    data_dict[key] = values
                except Exception as e:
                    print(
                        f"Warnung: {channel_name} in group {group_index} konnte nicht gelesen werden: {e}"
                    )
    all_data_dict[mf4_path] = data_dict

for path, channels in all_data_dict.items():
    print(f"{path}: {list(channels.keys())}")
