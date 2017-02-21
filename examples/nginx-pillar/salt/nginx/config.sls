my_config:
  file.managed:
    - name: /etc/nginx/sites-enabled/my_vhost.conf
    - user: root
    - group: root
    - mode: 644
    - source: salt://files/my_vhost_conf.jinja
    - template: jinja
    - context:
        env:
            server_name: dev.server.com
            log_prefix: dev_server_com
            backend_server: dev-myapp.server.com
        #env: {{ salt['pillar.get']('nginx') }}
    - require:
      - pkg: nginx

