#!/bin/bash

DB="app/db.sqlite3"
BASE="http://127.0.0.1:8000"

########################################
# START GAME TESTS
########################################

# ✅ start success
sqlite3 $DB "
DELETE FROM games WHERE id='test-start-success';
DELETE FROM players WHERE id IN ('host-player-123','player2-789');
INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-start-success','Test Game',2,NULL,'waiting','host-player-123','[\"host-player-123\",\"player2-789\"]');
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-player-123','Host Player','1990-09-15',NULL,'test-start-success'),
 ('player2-789','Player2','1995-01-01',NULL,'test-start-success');
"
curl -s -X POST $BASE/games/test-start-success/start -H "Content-Type: application/json" -d '{"player_id":"host-player-123"}' | jq .

# ❌ insufficient players
sqlite3 $DB "
DELETE FROM games WHERE id='test-insufficient-players';
DELETE FROM players WHERE id='host-alone';
INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-insufficient-players','Test Game',2,NULL,'waiting','host-alone','[\"host-alone\"]');
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-alone','Host Alone','1990-09-15',NULL,'test-insufficient-players');
"
curl -s -X POST $BASE/games/test-insufficient-players/start -H "Content-Type: application/json" -d '{"player_id":"host-alone"}' | jq .

# ❌ not owner
sqlite3 $DB "
DELETE FROM games WHERE id='test-ownership-validation';
DELETE FROM players WHERE id IN ('real-host','fake-host');
INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-ownership-validation','Test Game',2,NULL,'waiting','real-host','[\"real-host\",\"fake-host\"]');
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('real-host','Real Host','1990-09-15',NULL,'test-ownership-validation'),
 ('fake-host','Fake Host','1990-09-15',NULL,'test-ownership-validation');
"
curl -s -X POST $BASE/games/test-ownership-validation/start -H "Content-Type: application/json" -d '{"player_id":"fake-host"}' | jq .

# ❌ already started
sqlite3 $DB "
DELETE FROM games WHERE id='test-already-started';
DELETE FROM players WHERE id IN ('host-started','player2');
INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-already-started','Test Game',2,NULL,'playing','host-started','[\"host-started\",\"player2\"]');
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-started','Host Started','1990-09-15',NULL,'test-already-started'),
 ('player2','Player 2','1995-01-01',NULL,'test-already-started');
"
curl -s -X POST $BASE/games/test-already-started/start -H "Content-Type: application/json" -d '{"player_id":"host-started"}' | jq .

# ✅ birthday logic
sqlite3 $DB "
DELETE FROM games WHERE id='test-birthday-logic';
DELETE FROM players WHERE id IN ('host-far-birthday','player-close-birthday');
INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-birthday-logic','Birthday Test Game',2,NULL,'waiting','host-far-birthday','[\"host-far-birthday\",\"player-close-birthday\"]');
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-far-birthday','Host Far Birthday','1990-01-01',NULL,'test-birthday-logic'),
 ('player-close-birthday','Close Birthday Player','1995-09-16',NULL,'test-birthday-logic');
"
curl -s -X POST $BASE/games/test-birthday-logic/start -H "Content-Type: application/json" -d '{"player_id":"host-far-birthday"}' | jq .


########################################
# JOIN GAME TESTS
########################################

# ✅ join success
sqlite3 $DB "
DELETE FROM games WHERE id='test-join-success';
DELETE FROM players WHERE id IN ('host-player-join','new-joiner-player');
INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-join-success','Test Join',4,NULL,'waiting','host-player-join','[\"host-player-join\"]');
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-player-join','Host Join','1990-09-15',NULL,'test-join-success'),
 ('new-joiner-player','New Joiner','1992-05-10',NULL,NULL);
"
curl -s -X POST $BASE/games/test-join-success/join -H "Content-Type: application/json" -d '{"player_id":"new-joiner-player"}' | jq .

# ❌ game not found
sqlite3 $DB "
DELETE FROM players WHERE id='valid-player-not-found';
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('valid-player-not-found','Valid Player','1990-01-01',NULL,NULL);
"
curl -s -X POST $BASE/games/nonexistent-game-id/join -H "Content-Type: application/json" -d '{"player_id":"valid-player-not-found"}' | jq .

# ❌ player not found
sqlite3 $DB "
DELETE FROM games WHERE id='test-join-player-not-found';
DELETE FROM players WHERE id='host-player-not-found';
INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-join-player-not-found','Test Join',2,NULL,'waiting','host-player-not-found','[\"host-player-not-found\"]');
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-player-not-found','Host Join','1990-09-15',NULL,'test-join-player-not-found');
"
curl -s -X POST $BASE/games/test-join-player-not-found/join -H "Content-Type: application/json" -d '{"player_id":"nonexistent-player-id"}' | jq .

# ❌ game full
sqlite3 $DB "
DELETE FROM games WHERE id='test-join-full';
DELETE FROM players WHERE id IN ('host-full-game','existing-player','rejected-player');
INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-join-full','Full Game',2,NULL,'waiting','host-full-game','[\"host-full-game\",\"existing-player\"]');
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-full-game','Host Full','1990-09-15',NULL,'test-join-full'),
 ('existing-player','Existing Player','1995-01-01',NULL,'test-join-full'),
 ('rejected-player','Rejected','1993-08-20',NULL,NULL);
"
curl -s -X POST $BASE/games/test-join-full/join -H "Content-Type: application/json" -d '{"player_id":"rejected-player"}' | jq .

# ❌ game in progress
sqlite3 $DB "
DELETE FROM games WHERE id='test-join-in-progress';
DELETE FROM players WHERE id IN ('host-in-progress','player1','late-joiner');
INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-join-in-progress','Progress Game',2,NULL,'playing','host-in-progress','[\"host-in-progress\",\"player1\"]');
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-in-progress','Host Progress','1990-09-15',NULL,'test-join-in-progress'),
 ('player1','Player1','1995-01-01',NULL,'test-join-in-progress'),
 ('late-joiner','Late Joiner','1994-12-05',NULL,NULL);
"
curl -s -X POST $BASE/games/test-join-in-progress/join -H "Content-Type: application/json" -d '{"player_id":"late-joiner"}' | jq .

# ❌ game finished
sqlite3 $DB "
DELETE FROM games WHERE id='test-join-finished';
DELETE FROM players WHERE id IN ('host-finished','player1','very-late-joiner');
INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-join-finished','Finished Game',2,NULL,'finished','host-finished','[\"host-finished\",\"player1\"]');
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('host-finished','Host Finished','1990-09-15',NULL,'test-join-finished'),
 ('player1','Player1','1995-01-01',NULL,'test-join-finished'),
 ('very-late-joiner','Very Late Joiner','1996-03-15',NULL,NULL);
"
curl -s -X POST $BASE/games/test-join-finished/join -H "Content-Type: application/json" -d '{"player_id":"very-late-joiner"}' | jq .

########################################
# CARD TESTS
########################################

# ✅ Deal cards success
sqlite3 $DB "
DELETE FROM games WHERE id='test-deal-cards';
DELETE FROM players WHERE id IN ('deal-host','deal-player1','deal-player2');
DELETE FROM deck_cards WHERE game_id='test-deal-cards';
DELETE FROM player_hands WHERE game_id='test-deal-cards';

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-deal-cards','Deal Test Game',3,NULL,'playing','deal-host','[\"deal-host\",\"deal-player1\",\"deal-player2\"]');

INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('deal-host','Deal Host','1990-09-15',NULL,'test-deal-cards'),
 ('deal-player1','Deal Player 1','1995-01-01',NULL,'test-deal-cards'),
 ('deal-player2','Deal Player 2','1992-05-10',NULL,'test-deal-cards');

-- Add some deck cards (not dealt yet)
INSERT INTO deck_cards (game_id,card_id,is_dealt) VALUES
 ('test-deal-cards','card1',0),
 ('test-deal-cards','card2',0),
 ('test-deal-cards','card3',0),
 ('test-deal-cards','card4',0),
 ('test-deal-cards','card5',0),
 ('test-deal-cards','card6',0);
"
curl -s -X POST $BASE/games/test-deal-cards/deal -H "Content-Type: application/json" -d '{"player_id":"deal-host"}' | jq .

# ✅ Get own cards
sqlite3 $DB "
DELETE FROM games WHERE id='test-get-own-cards';
DELETE FROM players WHERE id IN ('own-host','own-player1');
DELETE FROM deck_cards WHERE game_id='test-get-own-cards';
DELETE FROM player_hands WHERE game_id='test-get-own-cards';

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-get-own-cards','Own Cards Game',2,NULL,'playing','own-host','[\"own-host\",\"own-player1\"]');

INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('own-host','Own Host','1990-09-15',NULL,'test-get-own-cards'),
 ('own-player1','Own Player 1','1995-01-01',NULL,'test-get-own-cards');

-- Add player hands with type and name columns
INSERT INTO player_hands (game_id,player_id,card_id,position,type,name) VALUES
 ('test-get-own-cards','own-host','card1',0,'detective','Holmes Card'),
 ('test-get-own-cards','own-host','card2',1,'detective','Watson Card');
"
curl -s -X GET "$BASE/games/player/cards/own-host" | jq .

# ✅ Get another player's own cards (each player can only see their own)
sqlite3 $DB "
DELETE FROM games WHERE id='test-get-other-cards';
DELETE FROM players WHERE id IN ('other-host','other-player1');
DELETE FROM deck_cards WHERE game_id='test-get-other-cards';
DELETE FROM player_hands WHERE game_id='test-get-other-cards';

INSERT INTO games (id,nameGame,num_players,password,status,host,players) VALUES
 ('test-get-other-cards','Other Cards Game',2,NULL,'playing','other-host','[\"other-host\",\"other-player1\"]');

INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('other-host','Other Host','1990-09-15',NULL,'test-get-other-cards'),
 ('other-player1','Other Player 1','1995-01-01',NULL,'test-get-other-cards');

-- Add cards for player1
INSERT INTO player_hands (game_id,player_id,card_id,position,type,name) VALUES
 ('test-get-other-cards','other-player1','card3',0,'detective','Poirot Card');
"
curl -s -X GET "$BASE/games/player/cards/other-player1" | jq .

# ❌ Player not found
curl -s -X GET $BASE/games/player/cards/nonexistent-player | jq .

# ❌ Player not in any game (no hands)
sqlite3 $DB "
DELETE FROM players WHERE id='orphan-player';
INSERT INTO players (id,username,birthdate,avatar,at_game) VALUES
 ('orphan-player','Orphan Player','1990-01-01',NULL,NULL);
"
curl -s -X GET $BASE/games/player/cards/orphan-player | jq .
