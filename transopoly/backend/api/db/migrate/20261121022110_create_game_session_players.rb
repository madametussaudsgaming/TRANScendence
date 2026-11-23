class CreateGameSessionPlayers < ActiveRecord::Migration[8.1]
  def change
    create_table :game_session_players do |t|
      t.references :game_session, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true
      t.integer :player_id, null: false

      t.timestamps
    end
    add_index :game_session_players, [:game_session_id, :user_id], unique: true
    add_index :game_session_players, [:game_session_id, :player_id], unique: true
  end
end
