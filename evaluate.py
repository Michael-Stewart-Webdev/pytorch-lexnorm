import torch
from config import *
from load_data import load_data
from model import *
from colorama import Fore, Back, Style

def print_sentence():
	pass

def evaluate_model(model, dev_iterator, ix_to_word, ix_to_tag, tag_to_ix, print_output=False):

	correct_preds = 0.0
	total_preds = 0.0
	total_correctable = 0.0

	max_tag_length = max([len(y) for y in tag_to_ix.keys()])

	with torch.no_grad():
		if print_output:
			print ""
			logger.info("Dev set evaluation: ")
		for (bi, (batch_x, batch_y)) in enumerate(dev_iterator):
			# Ignore batch if it is not the same size as the others (happens at the end sometimes)
			if len(batch_x) != cf.BATCH_SIZE:
				continue
			batch_x = batch_x.to(device)
			model.zero_grad()
			model.hidden = model.init_hidden()
			batch_x_lengths = []
			for x in batch_x:
				batch_x_lengths.append( np.nonzero(x).size(0) )

			# TODO: Make this a method of the lstm tagger class instead
			tag_scores = model(batch_x, batch_x_lengths)	

			#print tag_scores
		
			for i, sent in enumerate(batch_x):
				s = []

				if cf.MODEL_TYPE == S2S:
					for j, word_ix in enumerate(sent):
						if word_ix > 0:						
							pred = tag_scores[i][j]
							v, pi = pred.max(0)
							pi = pi.cpu().numpy()				# predicted index							
							ci = batch_y[i][j].cpu().numpy()	# correct index
						
							word_color = Style.BRIGHT if ci > 0 else Style.DIM
							tag_color = Fore.GREEN if ci == pi	 else Fore.RED
							if ci == 0:
								tag_color = Style.DIM
							s.append(word_color + ix_to_word[word_ix] + Style.DIM + (("/" + Style.RESET_ALL + tag_color + ix_to_tag[pi]) if ci > 0 else "") + Style.RESET_ALL)

							not_entity = tag_to_ix["O"] if "O" in tag_to_ix else 0
							if pi != 0 and ci == pi:
								correct_preds += 1						  
							if ci != 0:
								total_correctable += 1
							if pi != 0:
								total_preds += 1

				if cf.MODEL_TYPE == S21:			
					pred = tag_scores[i]
					v, pi = pred.max(0)
					pi = pi.cpu().numpy()			# predicted index							
					ci = batch_y[i].cpu().numpy()	# correct index

					tag_color = Fore.GREEN if ci == pi	 else Fore.RED
					s.append(tag_color + ix_to_tag[pi].ljust(max_tag_length + 2) + Style.RESET_ALL)
					for word in sent:
						if word > 0:
							s.append(ix_to_word[word])
					
					if ci == 0:
						tag_color = Style.DIM

					if pi != 0 and ci == pi:
						correct_preds += 1						  
					if ci != 0:
						total_correctable += 1
					if pi != 0:
						total_preds += 1
					


				if print_output and bi < 1: # Print first 1 dev batches only
					print " ".join(s)		


		if print_output:
			print ""		

		p = correct_preds / total_preds if correct_preds > 0 else 0
		r = correct_preds / total_correctable if correct_preds > 0 else 0
		f1 = 2 * p * r / (p + r) if correct_preds > 0 else 0
		
		print "-" * 100
		logger.info("F1 Score: %.4f" % f1)
		print "-" * 100

		return f1

		# logger.info("Generated sentences: ")
		# print " " * 6 + "=" * 60
		# for x in range(10):
		# 	sent = model.generate_sentence(ix_to_word)			
		# 	print " " * 6 + sent
		# print " " * 6 + "=" * 60
		# print ""

def main():
	data_iterator, glove_embeddings, word_to_ix, ix_to_word = load_data()

	model = LSTMTagger(cf.EMBEDDING_DIM, cf.HIDDEN_DIM, len(word_to_ix), cf.BATCH_SIZE, cf.MAX_SENT_LENGTH, glove_embeddings)
	model.cuda()
	model.load_state_dict(torch.load('asset/model_trained'))

	evaluate_model(model, ix_to_word)

if __name__ == '__main__':
	main()