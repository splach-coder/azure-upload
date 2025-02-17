import logging

test = {
		"apiVersion": "2024-11-30",
		"modelId": "Bleckman-voorblad-model",
		"stringIndexType": "utf16CodeUnit",
		"content": "B Bleckmann\nEXITCODE EX/EU/COZ\nBE212000\nEXITCODE T1/T2/T-\nKANTOOR DOORGANG\nCMR NR\nDATUM OPHALING\nBESTEMMELING\nBadger & Fox\nSG\nSITE\nCROSSWOODS\nMails\nDatum\nExitcode Mail\nTransport Mail\nM/V/K/S/L\nDKM\nOpmerkingen !!!!!\nEUR 1 ID:\nID: 6212643\nDATUM:\n12/feb\nMERK\nAB\nincoterm:\nEXW\nORDERNR\nIF0861935\nAANTAL DOZEN\n1\nBRUTO GEWICHT\n9,71\nNETTO GEWICHT\nB/NB\nNB\nTRANSPORT\nDHL EXPRESS\nTOTAAL DOZEN BONDED\nTOTAAL NON BONDED\nTOTAAL GEWICHT\nTOTAAL GEWICHT\nDOSSIER OK",
		"documents": [
			{
				"docType": "Bleckman-voorblad-model",
				"boundingRegions": [
					{
						"pageNumber": 1,
						"polygon": [
							0,
							0,
							8.2639,
							0,
							8.2639,
							11.6806,
							0,
							11.6806
						]
					}
				],
				"fields": {
					"ID": {
						"type": "string",
						"valueString": "6212643",
						"content": "6212643",
						"boundingRegions": [
							{
								"pageNumber": 1,
								"polygon": [
									2.5488,
									4.6923,
									3.202,
									4.6934,
									3.2017,
									4.8519,
									2.5485,
									4.8507
								]
							}
						],
						"confidence": 0.97,
						"spans": [
							{
								"offset": 229,
								"length": 7
							}
						]
					},
					"Exit Office": {
						"type": "string",
						"valueString": "BE212000",
						"content": "BE212000",
						"boundingRegions": [
							{
								"pageNumber": 1,
								"polygon": [
									3.1481,
									2.027,
									3.9212,
									2.0288,
									3.9208,
									2.1901,
									3.1477,
									2.1882
								]
							}
						],
						"confidence": 0.974,
						"spans": [
							{
								"offset": 31,
								"length": 8
							}
						]
					},
					"Voorblad_Items": {
						"type": "object",
						"valueObject": {
							"Collis": {
								"type": "object",
								"valueObject": {
									"one": {
										"type": "string",
										"valueString": "1",
										"content": "1",
										"boundingRegions": [
											{
												"pageNumber": 1,
												"polygon": [
													2.9967,
													6.4858,
													3.0704,
													6.485,
													3.0719,
													6.6242,
													2.9982,
													6.625
												]
											}
										],
										"confidence": 0.985,
										"spans": [
											{
												"offset": 304,
												"length": 1
											}
										]
									},
									"two": {
										"type": "string",
										"confidence": 0.995
									},
									"three": {
										"type": "string",
										"confidence": 0.995
									},
									"four": {
										"type": "string",
										"confidence": 0.995
									},
									"five": {
										"type": "string",
										"confidence": 0.995
									}
								},
								"confidence": 0.968
							},
							"Weight": {
								"type": "object",
								"valueObject": {
									"one": {
										"type": "string",
										"valueString": "9,71",
										"content": "9,71",
										"boundingRegions": [
											{
												"pageNumber": 1,
												"polygon": [
													2.8668,
													6.8393,
													3.1846,
													6.8368,
													3.1859,
													7.0019,
													2.8681,
													7.0044
												]
											}
										],
										"confidence": 0.982,
										"spans": [
											{
												"offset": 320,
												"length": 4
											}
										]
									},
									"two": {
										"type": "string",
										"confidence": 0.995
									},
									"three": {
										"type": "string",
										"confidence": 0.995
									},
									"four": {
										"type": "string",
										"confidence": 0.995
									},
									"five": {
										"type": "string",
										"confidence": 0.995
									}
								},
								"confidence": 0.962
							}
						},
						"confidence": 0.719
					}
				},
				"confidence": 0.999,
				"spans": [
					{
						"offset": 0,
						"length": 447
					}
				]
			}
		],
		"contentFormat": "text",
		"sections": [
			{
				"spans": [
					{
						"offset": 0,
						"length": 447
					}
				],
				"elements": [
					"/figures/0",
					"/tables/0",
					"/tables/1",
					"/paragraphs/18",
					"/paragraphs/19",
					"/paragraphs/20",
					"/paragraphs/21",
					"/paragraphs/22",
					"/tables/2",
					"/tables/3",
					"/paragraphs/42"
				]
			}
		],
		"figures": [
			{
				"id": "1.1",
				"boundingRegions": [
					{
						"pageNumber": 1,
						"polygon": [
							0.7711,
							0.9086,
							2.2029,
							0.9086,
							2.203,
							1.3958,
							0.7711,
							1.3958
						]
					}
				],
				"spans": [
					{
						"offset": 0,
						"length": 11
					}
				],
				"elements": [
					"/paragraphs/0"
				]
			}
		]
	}

document = test.get("documents")
result_dict = {}
fields = document[0].get("fields")
for key, value in fields.items():

    if key in ["Voorblad_Items"]:
        # Fields that contain arrays
        logging.error(value)
        arr = value.value
        result_dict[key] = []
        for item in arr:
            value_object = item.get("valueString")
            obj = {}
            for key_obj, value_obj in value_object.items():
                obj[key_obj] = value_obj.value
            result_dict[key].append(obj)
    else:
 
        result_dict[key] = value.get("valueString")

print(result_dict)