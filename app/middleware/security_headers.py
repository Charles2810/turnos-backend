def setup_security_headers(app):
    """
    Inyecta cabeceras HTTP de seguridad robustas en todas las respuestas
    para mitigar ataques comunes (XSS, Clickjacking, MIME-sniffing, etc.)
    según el estándar OWASP ASVS v4.0.
    """
    @app.after_request
    def add_security_headers(response):
        # Prevención de MIME Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevención de Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Filtro XSS legacy para navegadores antiguos
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Forzar HTTPS (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy restrictiva pero compatible con Swagger UI
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:;"
        )
        
        # Política de Referrer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Deshabilitar almacenamiento en caché de respuestas API sensibles
        if response.content_type and "application/json" in response.content_type:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            
        return response
