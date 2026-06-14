"""JSON:API (https://jsonapi.org) serialization utilities for REST API responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional


class JsonApiSerializer:
    """Serialize data according to JSON:API specification."""

    @staticmethod
    def serialize_single(
        data: Dict[str, Any],
        resource_type: str,
        resource_id: Optional[str | int] = None,
        links: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Serialize a single resource to JSON:API format.

        Args:
            data: The resource data (will be placed in attributes)
            resource_type: The resource type name (e.g., 'leagues', 'teams')
            resource_id: The resource ID (if None, tries to extract from data['id'])
            links: Optional links object (e.g., {'self': '/api/leagues/1'})
            meta: Optional meta information

        Returns:
            JSON:API formatted response dict
        """
        if resource_id is None:
            resource_id = data.get('id')

        response = {
            'data': {
                'type': resource_type,
                'id': str(resource_id) if resource_id else None,
                'attributes': data,
            }
        }

        if links:
            response['data']['links'] = links

        if meta:
            response['meta'] = meta

        return response

    @staticmethod
    def serialize_collection(
        items: List[Dict[str, Any]],
        resource_type: str,
        resource_id_key: str = 'id',
        links: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Serialize a collection of resources to JSON:API format.

        Args:
            items: List of resource dicts
            resource_type: The resource type name (e.g., 'leagues', 'teams')
            resource_id_key: The key in each item dict to use as resource ID
            links: Optional top-level links
            meta: Optional meta information (e.g., pagination, timestamp)

        Returns:
            JSON:API formatted response dict
        """
        data = []
        for item in items:
            resource_id = item.get(resource_id_key)
            resource = {
                'type': resource_type,
                'id': str(resource_id) if resource_id else None,
                'attributes': item,
            }
            data.append(resource)

        response = {'data': data}

        if links:
            response['links'] = links

        if meta:
            response['meta'] = meta

        return response

    @staticmethod
    def serialize_error(
        status: int,
        title: str,
        detail: Optional[str] = None,
        code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Serialize an error response to JSON:API format.

        Args:
            status: HTTP status code
            title: Short error title
            detail: Detailed error message
            code: Error code identifier

        Returns:
            JSON:API error response dict
        """
        error = {
            'status': str(status),
            'title': title,
        }

        if detail:
            error['detail'] = detail

        if code:
            error['code'] = code

        return {'errors': [error]}

    @staticmethod
    def add_timestamp(response: Dict[str, Any]) -> Dict[str, Any]:
        """Add timestamp to response meta section.

        Args:
            response: JSON:API response dict

        Returns:
            Response with timestamp added to meta
        """
        if 'meta' not in response:
            response['meta'] = {}

        response['meta']['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        return response

    @staticmethod
    def add_pagination(
        response: Dict[str, Any],
        total: int,
        page: int,
        page_size: int,
        base_url: str,
    ) -> Dict[str, Any]:
        """Add pagination info to response.

        Args:
            response: JSON:API response dict
            total: Total number of items
            page: Current page number (1-indexed)
            page_size: Items per page
            base_url: Base URL for pagination links

        Returns:
            Response with pagination added
        """
        if 'meta' not in response:
            response['meta'] = {}

        response['meta']['pagination'] = {
            'total': total,
            'page': page,
            'page-size': page_size,
            'total-pages': (total + page_size - 1) // page_size,
        }

        # Add pagination links
        if 'links' not in response:
            response['links'] = {}

        response['links']['self'] = f"{base_url}?page={page}&page-size={page_size}"

        if page > 1:
            response['links']['first'] = f"{base_url}?page=1&page-size={page_size}"
            response['links']['prev'] = f"{base_url}?page={page - 1}&page-size={page_size}"

        total_pages = (total + page_size - 1) // page_size
        if page < total_pages:
            response['links']['next'] = f"{base_url}?page={page + 1}&page-size={page_size}"
            response['links']['last'] = f"{base_url}?page={total_pages}&page-size={page_size}"

        return response
