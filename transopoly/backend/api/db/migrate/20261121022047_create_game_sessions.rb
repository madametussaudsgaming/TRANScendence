class CreateGameSessions < ActiveRecord::Migration[8.1]
  def change
    create_table :game_sessions do |t|
      t.references :host, null: false, foreign_key: { to_table: :users }
      # without this Postgres will look for a hosts table that doesnt exist, crashing this migration
      t.string :status, null: false, default: "waiting"
      t.string :python_game_id

      t.timestamps
    end
  end
end
