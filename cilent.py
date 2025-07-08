import logging
from typing import Any
from uuid import uuid4
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest, SendStreamingMessageRequest

async def main() -> None:
    PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'
    BASE_URL = 'http://localhost:10022'

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    async with httpx.AsyncClient(timeout=30.0) as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=BASE_URL)

        final_agent_card_to_use: AgentCard | None = None

        try:
            logger.info(f'Attempting to fetch public agent card from: {BASE_URL}{PUBLIC_AGENT_CARD_PATH}')
            public_card = await resolver.get_agent_card()
            logger.info('Successfully fetched public agent card:')
            logger.info(public_card.model_dump_json(indent=2, exclude_none=True))
            final_agent_card_to_use = public_card
            logger.info('Using PUBLIC agent card for client initialization (default).')

            if public_card.supportsAuthenticatedExtendedCard:
                try:
                    logger.info(f'Public card supports authenticated extended card. Attempting to fetch from: {BASE_URL}')
                    auth_headers_dict = {'Authorization': 'Bearer dummy-token-for-extended-card'}
                    extended_card = await resolver.get_agent_card(http_kwargs={'headers': auth_headers_dict})
                    logger.info('Successfully fetched authenticated extended agent card:')
                    logger.info(extended_card.model_dump_json(indent=2, exclude_none=True))
                    final_agent_card_to_use = extended_card
                    logger.info('Using AUTHENTICATED EXTENDED agent card for client initialization.')
                except Exception as e_extended:
                    logger.warning(f'Failed to fetch extended agent card: {e_extended}. Will proceed with public card.', exc_info=True)
            else:
                logger.info('Public card does not indicate support for an extended card. Using public card.')

        except Exception as e:
            logger.error(f'Critical error fetching public agent card: {e}', exc_info=True)
            raise RuntimeError('Failed to fetch the public agent card. Cannot continue.') from e

        client = A2AClient(httpx_client=httpx_client, agent_card=final_agent_card_to_use)
        logger.info('A2AClient initialized.')

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': 'write the hello world in python'}],
                'messageId': uuid4().hex,
            },
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))

        try:
            response = await client.send_message(request)
            print(response.model_dump(mode='json', exclude_none=True))
        except Exception as e:
            logger.error(f'Error sending message: {e}', exc_info=True)
            raise

        # Uncomment for streaming after confirming non-streaming works
        # streaming_request = SendStreamingMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))
        # try:
        #     stream_response = client.send_message_streaming(streaming_request)
        #     async for chunk in stream_response:
        #         print(chunk.model_dump(mode='json', exclude_none=True))
        # except Exception as e:
        #     logger.error(f'Error streaming message: {e}', exc_info=True)
        #     raise

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())