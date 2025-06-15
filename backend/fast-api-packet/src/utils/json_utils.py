import json
import logging


def process_json():
    with open("src/static/aws_op.json", "r") as f:
        data = json.load(f)
    
    state = ''
    conversation = ''
    print(data)
    for event in data:
        if 'detail' in event:
            print( '1')
            # print(event['detail'])
            detail = event.get('detail')
            print('THIS IS DETAIL')
            print(detail)
            if 'transcripts' in detail['eventBody']:
                print('2')
                transcripts = detail['eventBody'].get('transcripts')
                for transcript in transcripts:
                    print('3')
                    if transcript['channel'] == 'INTERNAL':
                        print('4')
                        if state == 'EXTERNAL' or state == '':
                            print('5')
                            conversation += '</student>' if state == 'EXTERNAL' else ''
                            conversation += '<advisor>'
                            state = 'INTERNAL'
                    else:
                        print('6')
                        if state == 'INTERNAL' or state == '':
                            print('7')
                            conversation += '</advisor>' if state == 'INTERNAL' else ''
                            conversation += '<student>'
                            state = 'EXTERNAL'
                    alternatives = transcript['alternatives']
                    for alt in alternatives:
                        print('8')
                        conversation += alt.get('transcript', '')
    

    # Print or save the conversation
    # print(conversation)
    
    return conversation





def create_conversation_grouped(transcripts):
    conversation = []
    current_channel = None
    current_texts = []

    for entry in transcripts:
        channel = entry['channel_label'].replace('ch_', 'channel_')
        text = entry['transcript'].strip()
        
        if channel != current_channel:
            # Save the previous block if exists
            if current_channel is not None:
                conversation.append(f"<{current_channel}>{' '.join(current_texts)}</{current_channel}>")
            # Start a new block
            current_channel = channel
            current_texts = [text]
        else:
            # Same channel, keep adding
            current_texts.append(text)

    # Save the last block
    if current_channel is not None and current_texts:
        conversation.append(f"<{current_channel}>{' '.join(current_texts)}</{current_channel}>")

    return ' '.join(conversation)