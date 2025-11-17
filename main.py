from eurofly import EuroflyClient

# --- Пример использования ---
if __name__ == "__main__":
    client = EuroflyClient()
    result = client.get_traffic()
    print(result)

    print("\n--- Pilots on ground ---")
    for pilot in result.pilots_on_ground[:10]:
        print(pilot, pilot.flight, pilot.url)

    print("\n--- Pilots in air ---")
    for pilot in result.pilots_in_air[:10]:
        print(pilot, pilot.flight, pilot.url)
