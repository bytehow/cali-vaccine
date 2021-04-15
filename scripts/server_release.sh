image=registry.digitalocean.com/cali-covid-vaccine/cali-covid-vaccine:latest
container_name=covid-bot

set +e

docker pull $image
docker rm -f $container_name
docker run -d --net host --name $container_name $image
docker logs -f $container_name
