# DO-challenge Back End

## Setup & Usage

### 1. Clone the Repository
```sh
git clone https://github.com/Biosim-AI/do-challenge
cd do-challenge/server
```

### 2. Start the Services
```sh
docker-compose up -d
```

### 3. Stop the Services
```sh
docker-compose down
```

### 4. Recreate Services & Apply Back-End Changes
```sh
docker-compose down -v
```
```sh
docker-compose up --build
```

### 5. Apply Back-End Code Changes
You can modify the code and restart the API container without rebuilding everything:
```sh
docker restart server-api-1 
```

### 5. View Logs
```sh
docker logs server-api-1
docker logs server-mongodb-1
```


### 6. Connect to MongoDB
```sh
mongodb://admin:admin_test@localhost:27017/do2025challenge
```

## Prerequisites
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

