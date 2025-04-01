from asammdf import MDF

try:
    with MDF("/home/andrae/Dokumente/10_git/20_ARES/sim_data/PO983_PT1104_Mue_2024-01-31 17_23_41.mf4") as mdf_file:
        for i, group in enumerate(mdf_file.groups):
            print(f"Kanalgruppe Index: {i}")
            print(f"  Name: {group.name}")  # Verfügbar in neueren asammdf Versionen
            print("  Enthaltene Kanäle:")
            for channel in group.channels:
                print(f"    - {channel.name}")
            print("-" * 20)

except FileNotFoundError:
    print("Die angegebene MF4-Datei wurde nicht gefunden.")
except Exception as e:
    print(f"Ein Fehler ist aufgetreten: {e}")