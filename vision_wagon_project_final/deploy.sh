
#!/bin/bash
case "$1" in
  deploy)
    echo "Deploying proyecto_integrado..."
    docker-compose up -d
    echo "Deployed successfully! Access at:"
    echo "- Frontend: http://localhost"
    echo "- Vision Wagon API: http://localhost:8000"
    echo "- Nómada Alpha API: http://localhost:8080"
    echo "- Grafana: http://localhost:3001"
    echo "- Prometheus: http://localhost:9090"
    ;;
  stop)
    echo "Stopping proyecto_integrado..."
    docker-compose down
    ;;
  *)
    echo "Usage: $0 {deploy|stop}"
    exit 1
    ;;
esac
