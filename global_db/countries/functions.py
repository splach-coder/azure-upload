from global_db.countries.countries import countries

def get_abbreviation_by_country(country_name):
    if country_name is None:
        return None
    for entry in countries:
        if entry["country"].lower() == country_name.lower():
            return entry["abbreviation"]
    return country_name