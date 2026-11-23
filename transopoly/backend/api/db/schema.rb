# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[8.1].define(version: 2026_11_21_022110) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "pg_catalog.plpgsql"

  create_table "game_session_players", force: :cascade do |t|
    t.bigint "game_session_id", null: false
    t.bigint "user_id", null: false
    t.integer "player_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["game_session_id", "player_id"], name: "index_game_session_players_on_game_session_id_and_player_id", unique: true
    t.index ["game_session_id", "user_id"], name: "index_game_session_players_on_game_session_id_and_user_id", unique: true
    t.index ["game_session_id"], name: "index_game_session_players_on_game_session_id"
    t.index ["user_id"], name: "index_game_session_players_on_user_id"
  end

  create_table "game_sessions", force: :cascade do |t|
    t.bigint "host_id", null: false
    t.string "status", default: "waiting", null: false
    t.string "python_game_id"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["host_id"], name: "index_game_sessions_on_host_id"
  end

  create_table "users", force: :cascade do |t|
    t.string "email", null: false
    t.string "password_digest", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["email"], name: "index_users_on_email", unique: true
  end

  add_foreign_key "game_session_players", "game_sessions"
  add_foreign_key "game_session_players", "users"
  add_foreign_key "game_sessions", "users", column: "host_id"
end
