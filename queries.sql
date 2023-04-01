# Query #1: Create stream for querying all youtube_videos - run this query in KsqlDB
CREATE STREAM youtube_videos (
  video_id VARCHAR KEY,
  title VARCHAR,
  views INTEGER,
  comments INTEGER,
  likes INTEGER
) WITH (
  KAFKA_TOPIC = 'youtube_videos',
  PARTITIONS = 1,
  VALUE_FORMAT = 'avro'
);

# Query #2: Create table for storing changes only - run this query in KsqlDB
CREATE TABLE youtube_changes WITH (KAFKA_TOPIC='youtube_changes') AS SELECT
  video_id,
  latest_by_offset(title) AS title,
  latest_by_offset(comments, 2)[1] AS comments_previous,
  latest_by_offset(comments, 2)[2] AS comments_current,
  latest_by_offset(views, 2)[1] AS views_previous,
  latest_by_offset(views, 2)[2] AS views_current,
  latest_by_offset(likes, 2)[1] AS likes_previous,
  latest_by_offset(likes, 2)[2] AS likes_current
FROM youtube_videos
GROUP BY video_id
EMIT CHANGES;

# Query #3: Create stream for telegram notifications
CREATE STREAM telegram_outbox(
  `chat_id` VARCHAR,
  `text` VARCHAR
  ) WITH (
    KAFKA_TOPIC = 'telegram_outbox',
    PARTITIONS = 1,
    VALUE_FORMAT = 'avro'
  ); 

# Query #4: Testing if http sink connector works with telegram bot
INSERT INTO telegram_outbox (
  `chat_id`,
  `text`
 ) VALUES (
   '495269410',
   'NEARLY THERE!'
   );

# Query #5: Creating a new youtube_changes but as stream instead of table
CREATE STREAM youtube_changes_stream WITH (KAFKA_TOPIC='youtube_changes', VALUE_FORMAT='avro');

# Query #6: Inserting into telegram_outbox when there is changes in video statistics
INSERT INTO telegram_outbox
SELECT
  '<your chat id>' AS `chat_id`,
  CONCAT(
    'Comments changed: ',
    CAST(comments_previous AS STRING),
    ' => ',
    CAST(comments_current AS STRING),
    '. ',
    title
  ) AS `text`
FROM youtube_changes_stream
WHERE comments_current <> likes_previous;