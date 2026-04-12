FROM nginx:alpine

# Remove default nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy site files
COPY ganz-dijital-FINAL.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css

# Copy nginx config template
COPY nginx.conf /etc/nginx/nginx.conf.template

EXPOSE 80

# Use envsubst to substitute $PORT at runtime, then start nginx
CMD sh -c "envsubst '\$PORT' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"
