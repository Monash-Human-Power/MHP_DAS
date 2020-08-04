#include <iostream>

#include <mqtt/message.h>

#include "protocol.hpp"
#include "mqtt.hpp"

void receive_callback(mqtt::const_message_ptr message)
{
    std::cout << "Parsed packet!" << std::endl
        << "\tQoS:      " << message->get_qos() << std::endl
        << "\tRetained: " << message->is_retained() << std::endl
        << "\tTopic:    " << message->get_topic() << std::endl
        << "\tPayload:  " << message->get_payload() << std::endl;
}

int main()
{
    auto mqttClient = std::make_shared<MqttBridgeClient>();

    Protocol protocol(mqttClient);

    auto message = mqtt::make_message("topic", "payload");
    auto packets = TxProtocol().packMessage(message);
    protocol.zetaRfPacketReceivedCallback(packets[0]);

    while (std::cin.get() != 'q')
        ;

    return 0;
}