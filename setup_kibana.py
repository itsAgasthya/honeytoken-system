import requests
import json

KIBANA_URL = "http://localhost:5601"
ELASTICSEARCH_URL = "http://localhost:9200"

def create_index_pattern():
    """Create index patterns for honeytoken logs"""
    patterns = [
        {
            "title": "honeytoken-access-*",
            "timeFieldName": "timestamp"
        },
        {
            "title": "honeytoken-alerts-*",
            "timeFieldName": "timestamp"
        }
    ]
    
    for pattern in patterns:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/index-pattern",
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            json=pattern
        )
        print(f"Created index pattern {pattern['title']}: {response.status_code}")

def create_visualizations():
    """Create visualizations for honeytoken monitoring"""
    visualizations = [
        {
            "attributes": {
                "title": "Access Attempts Over Time",
                "visState": json.dumps({
                    "type": "line",
                    "params": {
                        "addTimeMarker": False,
                        "addTooltip": True,
                        "categoryAxes": [{
                            "id": "CategoryAxis-1",
                            "labels": {"show": True, "truncate": 100},
                            "position": "bottom",
                            "scale": {"type": "linear"},
                            "show": True,
                            "style": {},
                            "title": {},
                            "type": "category"
                        }],
                        "grid": {"categoryLines": False, "style": {"color": "#eee"}},
                        "legendPosition": "right",
                        "seriesParams": [{
                            "data": {"id": "1", "label": "Count"},
                            "drawLinesBetweenPoints": True,
                            "mode": "normal",
                            "show": "true",
                            "showCircles": True,
                            "type": "line",
                            "valueAxis": "ValueAxis-1"
                        }],
                        "times": [],
                        "type": "line",
                        "valueAxes": [{
                            "id": "ValueAxis-1",
                            "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                            "name": "LeftAxis-1",
                            "position": "left",
                            "scale": {"mode": "normal", "type": "linear"},
                            "show": True,
                            "style": {},
                            "title": {"text": "Count"},
                            "type": "value"
                        }]
                    },
                    "aggs": [{
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    }, {
                        "id": "2",
                        "enabled": True,
                        "type": "date_histogram",
                        "schema": "segment",
                        "params": {
                            "field": "timestamp",
                            "timeRange": {"from": "now-7d", "to": "now"},
                            "useNormalizedEsInterval": True,
                            "interval": "auto",
                            "drop_partials": False,
                            "customInterval": "2h",
                            "min_doc_count": 1,
                            "extended_bounds": {}
                        }
                    }]
                })
            }
        },
        {
            "attributes": {
                "title": "Top Accessed Resources",
                "visState": json.dumps({
                    "type": "pie",
                    "params": {
                        "type": "pie",
                        "addTooltip": True,
                        "addLegend": True,
                        "legendPosition": "right",
                        "isDonut": True
                    },
                    "aggs": [{
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "schema": "metric",
                        "params": {}
                    }, {
                        "id": "2",
                        "enabled": True,
                        "type": "terms",
                        "schema": "segment",
                        "params": {
                            "field": "resource_type.keyword",
                            "size": 10,
                            "order": "desc",
                            "orderBy": "1"
                        }
                    }]
                })
            }
        }
    ]
    
    for viz in visualizations:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/visualization",
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            json=viz
        )
        print(f"Created visualization {viz['attributes']['title']}: {response.status_code}")

def create_dashboards():
    """Create Kibana dashboards"""
    dashboards = [
        {
            "attributes": {
                "title": "Honeytoken Access Overview",
                "hits": 0,
                "description": "Overview of honeytoken access attempts",
                "panelsJSON": json.dumps([
                    {
                        "gridData": {
                            "x": 0,
                            "y": 0,
                            "w": 24,
                            "h": 15,
                            "i": "1"
                        },
                        "version": "7.17.0",
                        "type": "visualization",
                        "id": "access-attempts-over-time"
                    },
                    {
                        "gridData": {
                            "x": 24,
                            "y": 0,
                            "w": 24,
                            "h": 15,
                            "i": "2"
                        },
                        "version": "7.17.0",
                        "type": "visualization",
                        "id": "top-accessed-resources"
                    }
                ])
            }
        }
    ]
    
    for dashboard in dashboards:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/dashboard",
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            json=dashboard
        )
        print(f"Created dashboard {dashboard['attributes']['title']}: {response.status_code}")

def main():
    """Set up Kibana dashboards and visualizations"""
    print("Setting up Kibana dashboards...")
    create_index_pattern()
    create_visualizations()
    create_dashboards()
    print("Setup complete!")

if __name__ == "__main__":
    main() 