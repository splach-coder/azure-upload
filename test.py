from ILS_NUMBER.get_ils_number import call_logic_app

response = call_logic_app("STANLEY", company="vp")
print(response)