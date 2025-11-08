FROM fiscoorg/fisco-bcos:latest
WORKDIR /app
COPY contract/ /app/contract/
COPY data/init_chain.sh /app/init_chain.sh
RUN chmod +x /app/init_chain.sh
EXPOSE 8545 30303
CMD ["/app/init_chain.sh"]
