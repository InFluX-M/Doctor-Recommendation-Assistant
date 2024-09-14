
# Setting up Elastic Search:
```
cd Search
docker cp {image_name}-es01-1:/usr/share/elasticsearch/config/certs .
```


# Setting up Files:

### in FastAPI/NLU/ directory

[model_metadata.json](https://ner-model.s3.ir-thr-at1.arvanstorage.ir/model_metadata.json)

[model.onnx](https://ner-model.s3.ir-thr-at1.arvanstorage.ir/model.onnx)

### in FastAPI/Search/ directory

[doctors.json](https://ner-model.s3.ir-thr-at1.arvanstorage.ir/doctors.json)

[cities.csv](https://ner-model.s3.ir-thr-at1.arvanstorage.ir/cities.csv)
