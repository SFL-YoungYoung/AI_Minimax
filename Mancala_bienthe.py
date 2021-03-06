#!/usr/bin/env python
'''
Lê Đức Dũng, Phạm Nhật Hải, Đồng Đan Hoài
Mancala AI Bot 
	Link tham thảo :https://github.com/138paulmiller/Mancala-AI-Bot (Mã nguồn)
	                https://www.mathplayground.com/mancala.html
					Target : 
'''
import multiprocessing
import random
import sys # used to catch interrupts

# use these variables for players to prevent error checking on board
DEBUG = True

class Board:
	def __init__(self, other=None):
		if other: #make copy
			self.board = [4,4,4,4,4,4,4,4,4,4,4,4]			
			for i in range(0, len(other.board)):			
				self.board[i] = other.board[i]
			self.bowl = [other.bowl[0], other.bowl[1]]
			self.move_num = other.move_num
		else:
			# player 0's side of board is board[0] and bowl[0]
			# Thiết lập bàn chơi:
			# Mỗi bên có 6 slot(mỗi slot có 6 pieces) và 2 bowl(dùng để tính điểm player)
			self.board = [4,4,4,4,4,4,4,4,4,4,4,4]
			self.bowl = [0,0]
			self.move_num = 0
 #sân chơi của 1  và 2 :D 

	def move(self, player, slot): #<Hoài_Done>
		# rải đá mỗi ô 1 viên đến cuối cùng vẫn tiếp tục khi
		# nó đi bth , bỏ qua ô quan của người khác	
		# viên đá cuối ở trong ô quan của bản thân, tiếp tục lượt chơi của mình
		# slot (0, 5), player (0,1)
		slot = slot + (player)*6; #định hình lại lĩnh vực của người chơi
		pieces = self.board[slot] #số đá
		self.board[slot] = 0 #khi mình cầm số đá tại ô slot
		
		###
		next_player = player
		while pieces > 0:
			slot = (slot+1)%12 #rải đến ô bao nhiêu
			# đối với ô quan của người chơi
			if slot == (player+1)*6%12:	# vị trí ô quan					
				self.bowl[player]+=1
				next_player = player
				pieces -= 1
			 # drop piece in players bowl
			# if pieces, continue dropping in slots
			if pieces > 0:
				# cộng thêm piece vào slot
				self.board[slot]+=1	
				next_player = (player+1)%2 # next player						
			pieces-=1			
			# if no more pieces, and on player side, add those pieces if >1(just added)
			# Nếu không còn đá, và trên sân người chơi, và trong ô đó không có đá thì sẽ ăn điểm ô đối diện
			if pieces == 0 and slot < (player+1)*6 and slot > (player)*6 and self.board[slot] == 1:
				slot = 11 - slot
				if self.board[slot] > 0:
					self.bowl[player] = self.bowl[player] + self.board[slot]
					self.board[slot] = 0
		self.move_num += 1
		return next_player
			
	def get_score(self, player):
		return self.bowl[player]	# số 	đá trong ô quan
	
	def check_move(self, player, move):
		return ( move >= 0 and move <= 6) and  0 != self.board[player*6+move] 
		#check
	def get_pieces(self, player):
		# điểm điểm đá
		pieces = 0
		for i in range(0, 6):
			pieces += self.board[player*6+i]
		return pieces 
	

	def has_move(self, player): #< Hải >
		#nếu mà người chơi không đi được nữa thì 
		i = 0
		while i < 6 and  self.board[(player)*6+i] == 0:
			i+=1
		# đến cuối cùng thì số đá ko = 0
		return i != 6

	def game_over(self):
		# game kết thúc :D  khi và chỉ khi  2 ô quan có tổng = 48  (4*6 + 4*6)
		return (self.bowl[0] + self.bowl[1]) == 48

	
	def __repr__(self): #chỉ là hiển lại cho người chơi coi Dũng
		layout = '--------------'+ str(self.move_num) + '---------------\n'	
		layout += 'P2:' + str(self.bowl[1]) + '      6 <-- 1   |\n       |'
		# show in reverse for player 1		
		for p in reversed(self.board[6:14]):
			layout += str(p) + ' '
		layout += '|                    \n\n       |'
		for p in self.board[0:6]:
			layout += str(p) + ' '
		layout += '|\n       |  1 --> 6      P1: ' + str(self.bowl[0]) + '\n--------------------------------'	
		return layout
	

class AI:
	def __init__(self, player, lookahead, relative_score= False, horde=False, relative_horde=False):
		self.player = player
		# other player to opponent
		self.opponent = (player+1)%2 #đối thủ
		self.search_count = 0 # is not locked, does not update in parallel move
		self.lookahead = lookahead
		self.board = None
		self.horde = horde #đánh giá số đá của bot  
		self.relative_score = relative_score 
		self.relative_horde = relative_horde #đánh giá đối thử	
	
	
	def eval_heuristic(self, board): #truy vết (#Dũng_done )
		score =  board.get_score(self.player)
		pieces = 0
		if self.horde:
			if self.relative_horde:
				pieces = (pieces - board.get_pieces(self.opponent))
			else:
				pieces = board.get_pieces(self.player)
		if self.relative_score:
			score = (score - board.get_score(self.opponent)) 
		return score + pieces
	

	def alphabeta(self, board, alpha, beta, player, depth):
		value = 0	
		# Lỗi : nó không đúng khi phân luồng, xâu chuỗi và chỉ hoạt động khi di chuyển nối tiếp
		self.search_count += 1	
		# xét hết không gian trạng thái để tìm được hướng đi tốt nhất	
		if board.game_over() or depth == 0:								
			value = self.eval_heuristic(board)
		elif player == self.player:
			cut = False
			value = -48
			i = 0
			while i < 6 and not cut:
				board_copy = Board(board)
				if board_copy.check_move(self.player, i):
					next_player = board_copy.move(self.player, i)	
					value = max(value, self.alphabeta(board_copy, alpha, beta, next_player, depth-1))
					alpha  = max(value, alpha)
					if alpha >= beta:
						cut = True
				else: 
					#ko di chuyển
					alpha = -48
				i+=1
		else: # về phía đối thủ
			cut = False
			value = 48
			i = 0 
			#đối với mỗi nước đi của đối thủ,kiểm tra xem nó có hợp lệ không, nếu có thì lấy giá trị của nước đi có thể tiếp theo
			while i < 6 and not cut:
				board_copy = Board(board)
				# nếu đó là 1 nước đi oke
				if board_copy.check_move(self.opponent, i): 
					next_player = board_copy.move(self.opponent, i)				
					value = min(value, self.alphabeta(board_copy, alpha, beta, next_player, depth-1))
					beta  = min(value, beta)
					if alpha >= beta:
						cut = True
				else: #nó không di chuyển
					beta = 48
				i+=1
		return value


	def get_move_score(self, move): #<Dũng>
		value = -50
		board_copy = Board(self.board)
		next_player = self.player		
		# repeats are prioritized by increasing score	
		while next_player == self.player and board_copy.check_move(self.player, move):			
			next_player = board_copy.move(self.player, move)
			#nếu người chơi tiếp theo không có nước đi, hãy đổi sang người chơi khác
			if not board_copy.has_move(self.player):
				next_player = (next_player+1)%2
			value = max(value, self.alphabeta(board_copy, -48, 48, next_player, self.lookahead))	
		return value
		

	def move_parallel(self, board): 
		move = 0
		#print('AI Thinking...')
		try:
			pool = multiprocessing.Pool(multiprocessing.cpu_count())		
			move = 0		
			self.board = board
			# map all possible plays to unpack
			scores = pool.map_async(unpack_get_move_score, [(self,0), (self,1), (self,2), (self,3), (self,4), (self,5)]).get(60)	
			scores = list(scores)			
			# allow keyboard intteruptions 
			for i in range(0, 6): # ignore first move, already chosen
				if scores[move] < scores[i]:
					move = i
		except KeyboardInterrupt:
			pool.terminate()
			sys.exit(-1)
		finally:
			pool.close()		
		pool.join()
		return move
	
	# Simple NON-parallel approach <hải> 
	def move_serial(self, board):
		alpha = -48
		beta = 48
		value = alpha
		i = move = 0
		# foreach move possible
		cut = False
		self.search_count = 0
		print ('AI Thinking...')
		# for each move, check if its valid, if so get the value of the next possible move
		while i < 6 and not cut:
			board_copy = Board(board)
			# if i is a valid move, else ignore
			if board_copy.check_move(self.player, i): 
				next_player = board_copy.move(self.player, i)
				# if the next player has no move, change to other player
				if not board_copy.has_move(self.player):
					next_player = (next_player+1)%2
				# get next max move
				value = max(value, self.alphabeta(board_copy, alpha, beta, next_player, self.lookahead))
				if alpha < value:
					alpha = value
					move = i
				if alpha > beta:
					cut = True
			i+=1
		print ('Searched ', self.search_count, ' possibilities' )
		return move

	def move(self, board, parallel):
		if parallel:
			return self.move_parallel(board)
		else:
			return self.move_serial(board)


#			 Helper functions
# upack the async map args , expecting (ai_obj, move)
def unpack_get_move_score(args):	
	score = args[0].get_move_score(args[1])
	return score


def get_user_move(board, player): #<Dũng_done> 
	#if DEBUG:   
	#	return random.randint(0,5)
	valid = False
	move = 0
	while not valid:
		try:
			# get move input (1-6), offset to index (0-5)
			move = input('      	P1 pick ')
			move = int(move)-1
			while move < 0 or move > 5:	
				print ('Chọn một số trong các số từ 1-6 ')
				move = int(	input('      	P1 pick '))-1
			valid = True
		except:
			if move == 'quit':
				valid = True
			else:
				print( 'chỉ chọn từ 1 đến 6 thôi')
				valid = False
	return move


def main():
	P1 = 0
	P2 = 1
	# multiprocess computaion
	parallel = True
	lookahead = 2 # Thiết lập độ sâu : tăng mức khó dễ ,....
	board = Board()
	# ai Player
	ai = AI(P2, lookahead)
	# thiết lập người chơi 2 đi đầu
	current_player = 1 
	next = 0
	move = 0
	while not board.game_over() and move != 'quit':		
		print (board)
		print ('\nP'+str(current_player+1) + '\'s Turn' )
		# nếu người chơi hiện tại di chuyển, else switch
		if board.has_move(current_player):
			# ko phải ai thì là lượt của bạn
			if current_player != ai.player:	
				move = ''
				next = current_player
				while current_player == next and board.has_move(current_player) and move != 'quit':
					move = get_user_move(board, current_player)					
					if not board.check_move(current_player, move) :
						print( 'No pieces', move	)
					if move != 'quit':
						next = board.move(current_player, move)					
						print( board)
						print ('Play again!')
						print ('\nP'+str(current_player+1) )
									
			else:
				# ai turn		
				move = ai.move(board, parallel)
				# get the move cho ai
				print ( '\tAI picked ', move+1	)		
				next = board.move(ai.player, move)
				# trong khi thằng ai ko còn lượt chơi thì ....
				while ai.player == next and board.has_move(ai.player) and move != 'quit':
					print (board	)			
					print ('\tAI Playing Again...')
					move = ai.move(board, parallel)
					print ('\tAI picked ', move+1	)		
					next = board.move(ai.player, move)	 
			# set cho đứa tiếp theo chơi		
			current_player = next
		else:
			print ('\n P'+str(current_player+1) + ' has no moves!')
			current_player = (current_player+1)%2
	
	# Khi game kết thúc 
	if move != 'quit':
		print (' 		FINAL')
		print (board)
		p1_score = board.get_score(P1)
		p2_score = board.get_score(P2)
		if p1_score > p2_score:
			print ('Player 1 Wins!')
		elif p1_score < p2_score:
			print ('Player 2 Wins!')
		else:
			print ('It\'s a tie !')
	print ('Goodbye!')
if __name__ == '__main__':
	main()  # user interactive
