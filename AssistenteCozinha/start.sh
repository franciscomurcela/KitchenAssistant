#!/bin/bash

# Lançar todos os processos em novos terminais
gnome-terminal --tab -- bash -c "cd Assistente/FusionEngine && java -jar FusionEngine.jar; exec bash"
sleep 5
gnome-terminal --tab -- bash -c "cd Assistente/mmiframeworkV2 && java -jar mmiframeworkV2.jar; exec bash"
sleep 5
gnome-terminal --tab -- bash -c "cd Assistente/ && source ~/miniconda3/bin/activate && conda activate rasa-env && rasa run --enable-api --cors='*'; exec bash"
sleep 5
gnome-terminal --tab -- bash -c "cd Assistente/WebAppAssistantV2/APP2/ && python3 app.py; exec bash"
sleep 5
gnome-terminal --tab -- bash -c "cd Assistente/WebAppAssistantV2/ && http-server -p 8082 -S -C cert.pem -K key.pem; exec bash"
sleep 15
gnome-terminal --tab -- bash -c "cd Avaliador/ && python3 loggerKit.py; exec bash"
sleep 5
gnome-terminal --tab -- bash -c "cd Avaliador/ && python3 loggerIM.py; exec bash"
sleep 5
gnome-terminal --tab -- bash -c "cd Avaliador/ && python3 data_manager.py; exec bash"
sleep 5
gnome-terminal \
--tab -- bash -c "cd Avaliador/ && source myenv/bin/activate && python3 assessment_manager.py; exec bash"
sleep 5
gnome-terminal --tab -- bash -c "cd Avaliador/ && python3 dashboard.py; exec bash"

# Abrir o navegador com a URL especificada
# https://127.0.0.1:8082/index.htm
# https://127.0.0.1:8082/appGui.htm
# http://127.0.0.1:5003/metrics
# Espera por comando do usuário
read -p "Pressione ENTER para encerrar os terminais criados..."

# Encerrando os processos específicos
echo "Encerrando os terminais criados..."
pkill -f "java -jar FusionEngine.jar"
pkill -f "java -jar mmiframeworkV2.jar"
pkill -f "rasa run --enable-api"
pkill -f "python3 app.py"
pkill -f "http-server -p 8082"
pkill -f "python3 loggerKit.py"
pkill -f "python3 loggerIM.py"
pkill -f "python3 data_manager.py"
pkill -f "python3 assessment_manager.py"
pkill -f "python3 dashboard.py"

echo "Todos os processos encerrados."


