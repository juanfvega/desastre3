#!/bin/bash

DB="app/db.sqlite3"
BASE="http://127.0.0.1:8000"

########################################
# CARD DEALING TESTS
########################################

# ✅ deal cards success (preparation state)
echo "=== Testing deal cards success ==="
sqlite3 $DB "
DELETE FROM deck_cards WHERE game_id='test-deal-success';
DELETE FROM player_hands WHERE game_id='test-deal-success';
DELETE FROM games WHERE id='test-deal-success';
DELETE FROM players WHERE id IN ('host-deal-success','player2-deal-success');

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-deal-success','Deal Success Game',2,NULL,'preparation','host-deal-success','[\"host-deal-success\",\"player2-deal-success\"]');

INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-deal-success','Host Deal','1990-09-15',NULL,'test-deal-success'),
 ('player2-deal-success','Player2 Deal','1995-01-01',NULL,'test-deal-success');

INSERT INTO deck_cards (game_id,type,name,in_deck,in_card_draft) VALUES
 ('test-deal-success','not_so_fast','Not so fast',1,0),
 ('test-deal-success','not_so_fast','Not so fast',1,0),
 ('test-deal-success','detective','Card 1',1,0),
 ('test-deal-success','detective','Card 2',1,0),
 ('test-deal-success','detective','Card 3',1,0),
 ('test-deal-success','detective','Card 4',1,0),
 ('test-deal-success','detective','Card 5',1,0),
 ('test-deal-success','detective','Card 6',1,0),
 ('test-deal-success','detective','Card 7',1,0),
 ('test-deal-success','detective','Card 8',1,0),
 ('test-deal-success','detective','Card 9',1,0),
 ('test-deal-success','detective','Card 10',1,0),
 ('test-deal-success','detective','Card 11',1,0),
 ('test-deal-success','detective','Card 12',1,0);
"
curl -s -X POST $BASE/games/test-deal-success/deal | jq .

# ❌ deal cards - game not found
echo "=== Testing deal cards - game not found ==="
curl -s -X POST $BASE/games/nonexistent-game/deal | jq .

# ❌ deal cards - wrong state (waiting instead of preparation)
echo "=== Testing deal cards - wrong state ==="
sqlite3 $DB "
DELETE FROM deck_cards WHERE game_id='test-deal-wrong-state';
DELETE FROM player_hands WHERE game_id='test-deal-wrong-state';
DELETE FROM games WHERE id='test-deal-wrong-state';
DELETE FROM players WHERE id IN ('host-wrong-state','player2-wrong-state');

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-deal-wrong-state','Wrong State Game',2,NULL,'waiting','host-wrong-state','[\"host-wrong-state\",\"player2-wrong-state\"]');

INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-wrong-state','Host Wrong','1990-09-15',NULL,'test-deal-wrong-state'),
 ('player2-wrong-state','Player2 Wrong','1995-01-01',NULL,'test-deal-wrong-state');
"
curl -s -X POST $BASE/games/test-deal-wrong-state/deal | jq .

# ❌ deal cards - no players
echo "=== Testing deal cards - no players ==="
sqlite3 $DB "
DELETE FROM deck_cards WHERE game_id='test-deal-no-players';
DELETE FROM player_hands WHERE game_id='test-deal-no-players';
DELETE FROM games WHERE id='test-deal-no-players';

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-deal-no-players','No Players Game',2,NULL,'preparation','host-no-players','[]');
"
curl -s -X POST $BASE/games/test-deal-no-players/deal | jq .

# ❌ deal cards - no cards in deck
echo "=== Testing deal cards - no cards in deck ==="
sqlite3 $DB "
DELETE FROM deck_cards WHERE game_id='test-deal-no-cards';
DELETE FROM player_hands WHERE game_id='test-deal-no-cards';
DELETE FROM games WHERE id='test-deal-no-cards';
DELETE FROM players WHERE id IN ('host-no-cards','player2-no-cards');

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-deal-no-cards','No Cards Game',2,NULL,'preparation','host-no-cards','[\"host-no-cards\",\"player2-no-cards\"]');

INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-no-cards','Host No Cards','1990-09-15',NULL,'test-deal-no-cards'),
 ('player2-no-cards','Player2 No Cards','1995-01-01',NULL,'test-deal-no-cards');
"
curl -s -X POST $BASE/games/test-deal-no-cards/deal | jq .

# ❌ deal cards - not enough 'Not so fast' cards
echo "=== Testing deal cards - not enough special cards ==="
sqlite3 $DB "
DELETE FROM deck_cards WHERE game_id='test-deal-no-special';
DELETE FROM player_hands WHERE game_id='test-deal-no-special';
DELETE FROM games WHERE id='test-deal-no-special';
DELETE FROM players WHERE id IN ('host-no-special','player2-no-special');

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-deal-no-special','No Special Game',2,NULL,'preparation','host-no-special','[\"host-no-special\",\"player2-no-special\"]');

INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-no-special','Host No Special','1990-09-15',NULL,'test-deal-no-special'),
 ('player2-no-special','Player2 No Special','1995-01-01',NULL,'test-deal-no-special');

INSERT INTO deck_cards (game_id,type,name,in_deck,in_card_draft) VALUES
 ('test-deal-no-special','not_so_fast','Not so fast',1,0),
 ('test-deal-no-special','detective','Card 1',1,0),
 ('test-deal-no-special','detective','Card 2',1,0),
 ('test-deal-no-special','detective','Card 3',1,0),
 ('test-deal-no-special','detective','Card 4',1,0),
 ('test-deal-no-special','detective','Card 5',1,0);
"
curl -s -X POST $BASE/games/test-deal-no-special/deal | jq .

########################################
# GET PLAYER CARDS TESTS
########################################

# ✅ get player cards success
echo "=== Testing get player cards success ==="
sqlite3 $DB "
DELETE FROM player_hands WHERE game_id='test-get-cards-success';
DELETE FROM games WHERE id='test-get-cards-success';
DELETE FROM players WHERE id IN ('host-get-cards','player2-get-cards');

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-get-cards-success','Get Cards Game',2,NULL,'playing','host-get-cards','[\"host-get-cards\",\"player2-get-cards\"]');

INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-get-cards','Host Get Cards','1990-09-15',NULL,'test-get-cards-success'),
 ('player2-get-cards','Player2 Get Cards','1995-01-01',NULL,'test-get-cards-success');

INSERT INTO player_hands (game_id,player_id,type,name) VALUES
 ('test-get-cards-success','host-get-cards','detective','Hercule Poirot'),
 ('test-get-cards-success','host-get-cards','not_so_fast','Not so fast'),
 ('test-get-cards-success','host-get-cards','event','Murder Weapon'),
 ('test-get-cards-success','player2-get-cards','detective','Miss Marple'),
 ('test-get-cards-success','player2-get-cards','not_so_fast','Not so fast'),
 ('test-get-cards-success','player2-get-cards','devious','Fake Alibi');
"
curl -s -X GET $BASE/games/player/cards/host-get-cards | jq .
curl -s -X GET $BASE/games/player/cards/player2-get-cards | jq .

# ✅ get player cards - empty hand
echo "=== Testing get player cards - empty hand ==="
sqlite3 $DB "
DELETE FROM player_hands WHERE game_id='test-get-cards-empty';
DELETE FROM games WHERE id='test-get-cards-empty';
DELETE FROM players WHERE id='player-empty-hand';

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-get-cards-empty','Empty Hand Game',2,NULL,'playing','player-empty-hand','[\"player-empty-hand\"]');

INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('player-empty-hand','Player Empty','1990-09-15',NULL,'test-get-cards-empty');
"
curl -s -X GET $BASE/games/player/cards/player-empty-hand | jq .

# Test with nonexistent player (should return empty array)
echo "=== Testing get player cards - nonexistent player ==="
curl -s -X GET $BASE/games/player/cards/nonexistent-player | jq .

########################################
# INTEGRATION TESTS
########################################

# ✅ complete flow: deal cards then get cards
echo "=== Testing complete flow: deal then get ==="
sqlite3 $DB "
DELETE FROM deck_cards WHERE game_id='test-complete-flow';
DELETE FROM player_hands WHERE game_id='test-complete-flow';
DELETE FROM games WHERE id='test-complete-flow';
DELETE FROM players WHERE id IN ('host-complete','player2-complete');

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-complete-flow','Complete Flow Game',2,NULL,'preparation','host-complete','[\"host-complete\",\"player2-complete\"]');

INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-complete','Host Complete','1990-09-15',NULL,'test-complete-flow'),
 ('player2-complete','Player2 Complete','1995-01-01',NULL,'test-complete-flow');

INSERT INTO deck_cards (game_id,type,name,in_deck,in_card_draft) VALUES
 ('test-complete-flow','not_so_fast','Not so fast',1,0),
 ('test-complete-flow','not_so_fast','Not so fast',1,0),
 ('test-complete-flow','detective','Hercule Poirot',1,0),
 ('test-complete-flow','detective','Miss Marple',1,0),
 ('test-complete-flow','detective','Inspector Clouseau',1,0),
 ('test-complete-flow','event','Murder Weapon',1,0),
 ('test-complete-flow','event','Crime Scene',1,0),
 ('test-complete-flow','devious','Fake Alibi',1,0),
 ('test-complete-flow','devious','False Evidence',1,0),
 ('test-complete-flow','detective','Sherlock Holmes',1,0),
 ('test-complete-flow','detective','Sam Spade',1,0),
 ('test-complete-flow','detective','Philip Marlowe',1,0),
 ('test-complete-flow','event','Witness Statement',1,0),
 ('test-complete-flow','event','Police Report',1,0);
"

echo "--- Dealing cards ---"
curl -s -X POST $BASE/games/test-complete-flow/deal | jq .

echo "--- Getting host cards ---"
curl -s -X GET $BASE/games/player/cards/host-complete | jq .

echo "--- Getting player2 cards ---"
curl -s -X GET $BASE/games/player/cards/player2-complete | jq .

echo "--- Checking database state ---"
sqlite3 $DB "
SELECT 'Cards remaining in deck:' as info, COUNT(*) as count FROM deck_cards WHERE game_id='test-complete-flow' AND in_deck=1;
SELECT 'Cards in player hands:' as info, COUNT(*) as count FROM player_hands WHERE game_id='test-complete-flow';
SELECT 'Cards per player:' as info, player_id, COUNT(*) as count FROM player_hands WHERE game_id='test-complete-flow' GROUP BY player_id;
"

echo "=== Manual card tests completed ==="
