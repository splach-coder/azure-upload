from global_db.countries.countries import countries

def get_abbreviation_by_country(country_name):
    for entry in countries:
        if entry["country"].lower() == country_name.lower():
            return entry["abbreviation"]
    return country_name