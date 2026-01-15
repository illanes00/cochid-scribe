#!/bin/bash
# Run with: sudo bash /srv/projects/illanes00-scribe/deploy/setup-caddy.sh

set -e

echo "Adding scribe to Caddyfile..."

if grep -q 'scribe.illanes00.cl' /etc/caddy/Caddyfile 2>/dev/null; then
    echo "scribe.illanes00.cl already in Caddyfile"
else
    cat >> /etc/caddy/Caddyfile << 'EOF'

# illanes00-kiosk (Next.js)
kiosk.illanes00.cl {
	reverse_proxy localhost:8130
	encode gzip
	tls {
		dns cloudflare RWIdH2pmyguysRM73vnhT_JxvCcjSbA3IKgfu3OP
	}
	header Permissions-Policy "interest-cohort=()"
}

# illanes00-scribe (Full-stack app)
scribe.illanes00.cl {
	encode gzip
	tls {
		dns cloudflare RWIdH2pmyguysRM73vnhT_JxvCcjSbA3IKgfu3OP
	}
	header Permissions-Policy "interest-cohort=()"
	
	# API routes go to backend
	@api path /api/* /health /api/docs /api/redoc /api/openapi.json
	reverse_proxy @api localhost:8132
	
	# Everything else goes to frontend
	reverse_proxy localhost:8133
}
EOF
    echo "Added scribe and kiosk to Caddyfile"
fi

echo "Validating Caddy config..."
caddy validate --config /etc/caddy/Caddyfile

echo "Reloading Caddy..."
systemctl reload caddy

echo "Done! Testing health endpoints..."
sleep 2
curl -sf http://localhost:8132/health && echo ''
curl -sf -o /dev/null -w 'Frontend: %{http_code}\n' http://localhost:8133/
