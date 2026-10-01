class CreateGameSessions < ActiveRecord::Migration[7.0]
	def change
		create_table :gameSessions do |t|
			t.references :host,
						null: false,
						foreignKey: { toTable: :users }
			
			t.string :status,
					null: false,
					default: "waiting"

			t.string :pythonGameId
			t.timestamps
		end
	end
end