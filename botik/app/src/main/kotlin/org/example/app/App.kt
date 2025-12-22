package org.botmain.app

import com.github.kotlintelegrambot.bot
import com.github.kotlintelegrambot.dispatch
import com.github.kotlintelegrambot.dispatcher.text
import com.github.kotlintelegrambot.entities.ChatId

fun main() {
    val bot = bot {
        token = "8175695993:AAHJWBTzbDBEEy1BDKsApFIy3q9bJYciKCo"

        dispatch {
            text {
                bot.sendMessage(
                    chatId = ChatId.fromId(message.chat.id),
                    messageThreadId = message.messageThreadId,
                    text = text,
                    protectContent = true,
                    disableNotification = false,
                )
            }
        }
    }

    bot.startPolling()
}