### Setting up Speech Recognition
download [ffmpeg](https://ffmpeg.org/download.html#build-windows)
or
```
sudo apt-get install ffmpeg
```

### Setting up Elastic Search:
```
cd Search
docker-compose up -d
docker cp search-es01-1:/usr/share/elasticsearch/config/certs .
```